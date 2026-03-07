import logging
import os
import re
import sys
import uuid

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from openai import AuthenticationError, RateLimitError, APIError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.settings import BASE_DIR

logger = logging.getLogger(__name__)

VECTOR_STORAGE_PATH = os.path.join(BASE_DIR, 'vector_stores')
os.makedirs(VECTOR_STORAGE_PATH, exist_ok=True)

DEFAULT_HF_MODEL = 'sentence-transformers/all-mpnet-base-v2'

DEFAULT_PROMPT = ChatPromptTemplate.from_messages([
    ('human', 'Context:\n{context}\n\nQuestion: {input}'),
])


def _build_embeddings_model(model, api_key, api_url_base, hf_api_token, hf_model):
    if hf_api_token:
        return HuggingFaceEndpointEmbeddings(
            model=hf_model,
            task='feature-extraction',
            huggingfacehub_api_token=hf_api_token
        )
    return OpenAIEmbeddings(model=model, openai_api_base=api_url_base, openai_api_key=api_key)


def create_and_store_embeddings(source_text, model='text-embedding-3-large', api_key=None,
                                api_url_base=None, hf_api_token=None, hf_model=DEFAULT_HF_MODEL):
    file_id = str(uuid.uuid4())
    storage_path = os.path.join(VECTOR_STORAGE_PATH, file_id)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    docs = text_splitter.split_text(text=source_text)
    try:
        embeddings_model = _build_embeddings_model(model, api_key, api_url_base, hf_api_token, hf_model)
        vector_store = FAISS.from_texts(docs, embeddings_model)
        vector_store.save_local(storage_path)
    except AuthenticationError as e:
        logger.exception(e)
        raise ValueError('Invalid API key or authentication error.') from e
    except RateLimitError as e:
        logger.exception(e)
        raise RuntimeError('API rate limit exceeded, please try again later') from e
    except APIError as e:
        logger.exception(e)
        raise RuntimeError('OpenAI server error.') from e
    except Exception as e:
        logger.exception(e)
        raise RuntimeError('Failed to create vector store.') from e

    return file_id


def get_answer_with_embeddings(question, file_uuid, embedding_model='text-embedding-3-large', model='gpt-3.5-turbo',
                               instructions='', api_key=None, api_url_base=None, hf_api_token=None,
                               hf_model=DEFAULT_HF_MODEL):
    storage_path = os.path.join(VECTOR_STORAGE_PATH, file_uuid)

    if not os.path.exists(storage_path):
        raise FileNotFoundError(f"Store with UUID '{file_uuid}' not found.")

    embeddings_model = _build_embeddings_model(embedding_model, api_key, api_url_base, hf_api_token, hf_model)

    vector_store = FAISS.load_local(
        storage_path,
        embeddings_model,
        allow_dangerous_deserialization=True
    )

    llm = ChatOpenAI(model_name=model, temperature=0, openai_api_base=api_url_base, openai_api_key=api_key)

    prompt = ChatPromptTemplate.from_messages([
        ('system', instructions),
        ('human', 'Context:\n{context}\n\nQuestion: {input}'),
    ]) if instructions else DEFAULT_PROMPT

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    retriever = vector_store.as_retriever(
        search_type='mmr',
        search_kwargs={'k': 6, 'fetch_k': 20},
    )
    qa_chain = create_retrieval_chain(retriever, question_answer_chain)
    response = qa_chain.invoke({'input': question})
    return response.get('answer')


_CODE_BLOCK_RE = re.compile(
    r'(```[\s\S]*?```'        # fenced code blocks
    r'|`[^`\n]+`'             # inline code
    r'|(?:^\|.+\|[ \t]*\n)+'  # consecutive markdown table rows
    r')',
    re.MULTILINE,
)


def _split_preserving_code_blocks(text: str, chunk_size: int, chunk_overlap: int,
                                   splitter: RecursiveCharacterTextSplitter) -> list[str]:
    """Split text into chunks without ever breaking code blocks."""
    if len(text) <= chunk_size or not _CODE_BLOCK_RE.search(text):
        return splitter.split_text(text)

    # Tokenise: alternate between prose segments and code blocks
    tokens = _CODE_BLOCK_RE.split(text)   # [prose, code, prose, code, ...]
    code_blocks = _CODE_BLOCK_RE.findall(text)

    result: list[str] = []
    buffer = ''

    for i, prose in enumerate(tokens):
        if len(buffer) + len(prose) <= chunk_size:
            buffer += prose
        else:
            if buffer.strip():
                result.extend(splitter.split_text(buffer))
            buffer = prose

        if i < len(code_blocks):
            code = code_blocks[i]
            if len(buffer) + len(code) <= chunk_size * 1.5:
                buffer += code
            else:
                if buffer.strip():
                    result.extend(splitter.split_text(buffer))
                result.append(code)   # code block becomes its own chunk even if large
                buffer = ''

    if buffer.strip():
        result.extend(splitter.split_text(buffer))

    return result or [text]


def _get_parent_breadcrumb(metadata: dict) -> str:
    """Return the breadcrumb of the parent header (all levels except the deepest)."""
    parts = [metadata[k] for k in ('h1', 'h2', 'h3', 'h4') if metadata.get(k)]
    return ' > '.join(parts[:-1]) if len(parts) > 1 else ''


def _build_summary_chunk(source_text: str) -> str:
    """Build a document overview chunk from h1/h2/h3 headings."""
    heading_re = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
    lines = []
    for match in heading_re.finditer(source_text):
        level = len(match.group(1))
        indent = '  ' * (level - 1)
        lines.append(f'{indent}- {match.group(2).strip()}')
    if not lines:
        return ''
    return '[Document Overview]\n\n' + '\n'.join(lines)


def _split_markdown_docs(source_text: str, chunk_size: int = 2000,
                         chunk_overlap: int = 200) -> list[str]:
    """
    Smart chunking for Markdown documentation:

    1. Split by headers (##/###/####) — each section gets full breadcrumb path.
    2. Code blocks and markdown tables are never split.
    3. Small sibling sections (same parent header) are merged if combined < chunk_size.
    4. Oversized sections are split by paragraphs/lines while protecting code blocks.
    5. The breadcrumb is prepended to every chunk so the LLM always knows the context.
    6. A summary/index chunk is generated from h1/h2/h3 headings.
    """
    headers_to_split_on = [
        ('#', 'h1'),
        ('##', 'h2'),
        ('###', 'h3'),
        ('####', 'h4'),
    ]
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=['\n\n', '\n', ' '],
    )

    header_docs = md_splitter.split_text(source_text)

    # --- Merge small sibling sections ---
    merged_docs = []
    i = 0
    while i < len(header_docs):
        doc = header_docs[i]
        content = doc.page_content.strip()
        metadata = dict(doc.metadata)
        parent = _get_parent_breadcrumb(metadata)

        # Try merging with following siblings that share the same parent
        while (i + 1 < len(header_docs)
               and _get_parent_breadcrumb(header_docs[i + 1].metadata) == parent
               and parent  # only merge if there IS a parent (not top-level)
               and len(content) + len(header_docs[i + 1].page_content) + 2 < chunk_size):
            i += 1
            content = content + '\n\n' + header_docs[i].page_content.strip()

        merged_docs.append((metadata, content))
        i += 1

    # --- Build final chunks ---
    final_chunks: list[str] = []

    # Summary chunk
    summary = _build_summary_chunk(source_text)
    if summary:
        final_chunks.append(summary)

    for metadata, content in merged_docs:
        if not content:
            continue

        breadcrumb_parts = [
            metadata[k]
            for k in ('h1', 'h2', 'h3', 'h4')
            if metadata.get(k)
        ]
        breadcrumb = ' > '.join(breadcrumb_parts)
        prefix = f'[{breadcrumb}]\n\n' if breadcrumb else ''

        if len(prefix) + len(content) <= chunk_size:
            final_chunks.append(prefix + content)
        else:
            sub_chunks = _split_preserving_code_blocks(content, chunk_size, chunk_overlap, text_splitter)
            for chunk in sub_chunks:
                final_chunks.append(prefix + chunk)

    return final_chunks


def create_docs_embeddings(source_text: str, model: str = 'text-embedding-3-large',
                           api_key: str = None, api_url_base: str = None,
                           hf_api_token: str = None, hf_model: str = DEFAULT_HF_MODEL,
                           chunk_size: int = 2000, chunk_overlap: int = 200) -> str:
    """
    Docs mode: creates a vector store optimised for Markdown documentation.

    Differences from create_and_store_embeddings:
    - Header-aware chunking: sections are never split mid-heading.
    - Code blocks are treated as atomic units and never broken across chunks.
    - Each chunk is prefixed with the breadcrumb path (h1 > h2 > h3) so
      the retriever can find the right section even for context-free queries.

    Returns the UUID of the saved vector store.
    """
    file_id = str(uuid.uuid4())
    storage_path = os.path.join(VECTOR_STORAGE_PATH, file_id)

    docs = _split_markdown_docs(source_text, chunk_size, chunk_overlap)
    logger.info('Docs mode: %d chunks created from markdown source', len(docs))

    try:
        embeddings_model = _build_embeddings_model(model, api_key, api_url_base, hf_api_token, hf_model)
        vector_store = FAISS.from_texts(docs, embeddings_model)
        vector_store.save_local(storage_path)
    except AuthenticationError as e:
        logger.exception(e)
        raise ValueError('Invalid API key or authentication error.') from e
    except RateLimitError as e:
        logger.exception(e)
        raise RuntimeError('API rate limit exceeded, please try again later') from e
    except APIError as e:
        logger.exception(e)
        raise RuntimeError('OpenAI server error.') from e
    except Exception as e:
        logger.exception(e)
        raise RuntimeError('Failed to create vector store.') from e

    return file_id


if __name__ == '__main__':
    knowledge_base_text = """
    История компании "ТехноСферы".
    Компания "ТехноСфера" была основана в 2015 году тремя инженерами:
    Анной Волковой, Петром Сидоровым и Иваном Кузнецовым.
    Их целью было создание инновационных решений в области облачных вычислений.
    Первым успешным продуктом компании стала платформа "Облако-1", выпущенная в 2017 году.
    Она позволяла малым и средним предприятиям легко масштабировать свою IT-инфраструктуру.
    Главный офис компании находится в Москве. В 2022 году компания открыла филиал в Санкт-Петербурге.
    Финансовым директором с 2020 года является Елена Михайлова.
    """

    API_URL_BASE = 'https://routerai.ru/api/v1'
    API_KEY = ''
    MODEL_NAME = 'minimax/minimax-m2.5'
    EMBEDDING_MODEL_NAME = 'openai/text-embedding-3-large'
    HF_API_TOKEN = ''

    # ── Normal mode ──────────────────────────────────────────────────────────
    # saved_uuid = create_and_store_embeddings(
    #     knowledge_base_text,
    #     api_key=API_KEY,
    #     api_url_base=API_URL_BASE,
    #     hf_api_token=HF_API_TOKEN
    # )
    # saved_uuid = 'e20c695e-fdd5-4444-b4ec-be701d613b45'

    # ── Docs mode (Smart breakdown for MD documentation) ───────────────────────
    doc_file_path = '/var/www/api2app-frontend/docs/JSON_FORMAT.md'
    with open(doc_file_path, 'r', encoding='utf-8') as f:
        docs_md = f.read()

    # View chunks without creating an index:
    chunks = _split_markdown_docs(docs_md)
    print(f"--- Docs mode: {len(chunks)} chunks ---")
    for i, c in enumerate(chunks, 1):
        print(f"\n[chunk {i}]\n{c}")

    # Create a real index:
    saved_uuid = create_docs_embeddings(
        docs_md,
        api_key=API_KEY,
        api_url_base=API_URL_BASE,
        model=EMBEDDING_MODEL_NAME
    )
    print(f"Docs knowledge base UUID: {saved_uuid}")

    user_question = "О чём контекст?"
    answer = get_answer_with_embeddings(
        user_question,
        saved_uuid,
        model=MODEL_NAME,
        api_key=API_KEY,
        api_url_base=API_URL_BASE,
        hf_api_token=HF_API_TOKEN,
        embedding_model=EMBEDDING_MODEL_NAME
    )

    print(f"Question: {user_question}")
    print(f"Answer: {answer}")
