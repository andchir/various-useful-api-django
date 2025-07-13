import os
import sys
import uuid
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.text_splitter import RecursiveCharacterTextSplitter

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.settings import BASE_DIR

VECTOR_STORAGE_PATH = os.path.join(BASE_DIR, 'vector_stores')
os.makedirs(VECTOR_STORAGE_PATH, exist_ok=True)


def create_and_store_embeddings(source_text, model='text-embedding-ada-002', api_key=None, api_url_base=None):
    file_id = str(uuid.uuid4())
    storage_path = os.path.join(VECTOR_STORAGE_PATH, file_id)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    docs = text_splitter.split_text(text=source_text)
    embeddings_model = OpenAIEmbeddings(model=model, openai_api_base=api_url_base, openai_api_key=api_key)
    vector_store = FAISS.from_texts(docs, embeddings_model)
    vector_store.save_local(storage_path)

    return file_id


def get_answer_with_embeddings(question, file_uuid, embedding_model='text-embedding-ada-002',
                               model='gpt-3.5-turbo', api_key=None, api_url_base=None):
    storage_path = os.path.join(VECTOR_STORAGE_PATH, file_uuid)

    if not os.path.exists(storage_path):
        raise Exception(f'Error: Store with UUID \'{file_uuid}\' not found.')

    embeddings_model = OpenAIEmbeddings(model=embedding_model, openai_api_base=api_url_base, openai_api_key=api_key)

    vector_store = FAISS.load_local(
        storage_path,
        embeddings_model,
        allow_dangerous_deserialization=True
    )

    llm = ChatOpenAI(model_name=model, temperature=0.7, openai_api_base=api_url_base, openai_api_key=api_key)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=vector_store.as_retriever()
    )

    response = qa_chain.invoke({'query': question})

    return response.get('result')


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
    API_URL_BASE = 'https://api.openai.com/v1/'
    MODEL_NAME = 'gpt-3.5-turbo'

    # print("--- Создание базы знаний ---")
    # saved_uuid = create_and_store_embeddings(
    #     knowledge_base_text,
    #     api_key=API_KEY,
    #     api_url_base=API_URL_BASE
    # )
    # print(f"База знаний сохранена с UUID: {saved_uuid}\n")

    print("--- Получение ответа из базы знаний ---")
    user_question = "Кто основал компанию ТехноСфера и в каком году?"
    answer = get_answer_with_embeddings(
        user_question,
        'ea4ccf0d-953b-4088-8433-d72ee7064422',
        model=MODEL_NAME,
        api_key=API_KEY,
        api_url_base=API_URL_BASE
    )

    print(f"❓ Вопрос: {user_question}")
    print(f"🤖 Ответ: {answer}")

