import logging
import os
import sys
import uuid

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
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


def create_and_store_embeddings(source_text, model='text-embedding-ada-002', api_key=None,
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


def get_answer_with_embeddings(question, file_uuid, embedding_model='text-embedding-ada-002', model='gpt-3.5-turbo',
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
    qa_chain = create_retrieval_chain(vector_store.as_retriever(), question_answer_chain)
    response = qa_chain.invoke({'input': question})
    return response.get('answer')


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

    API_KEY = ''
    API_URL_BASE = 'https://provider.name/api/v2/openai/v1/'
    MODEL_NAME = 'gpt-3.5-turbo'
    HF_API_TOKEN = ''

    # print("--- Создание базы знаний ---")
    # saved_uuid = create_and_store_embeddings(
    #     knowledge_base_text,
    #     api_key=API_KEY,
    #     api_url_base=API_URL_BASE,
    #     hf_api_token=HF_API_TOKEN
    # )
    # print(f"База знаний сохранена с UUID: {saved_uuid}\n")
    saved_uuid = 'e20c695e-fdd5-4444-b4ec-be701d613b45'

    print("--- Получение ответа из базы знаний ---")
    user_question = "Кто основал компанию ТехноСфера и в каком году?"
    answer = get_answer_with_embeddings(
        user_question,
        saved_uuid,
        model=MODEL_NAME,
        api_key=API_KEY,
        api_url_base=API_URL_BASE,
        hf_api_token=HF_API_TOKEN
    )

    print(f"❓ Вопрос: {user_question}")
    print(f"🤖 Ответ: {answer}")
