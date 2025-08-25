import streamlit as st
from llm_connector import LLMConnector
from vector_store_pg import VectorStore
from document_processor import process_folder
from config import DATA_DIR, MODEL_DIR, DB_PARAMS
from pathlib import Path
import os


# --- Инициализация системы ---
def initialize_system():
    """Инициализация всех компонентов с проверками"""

    # Проверка папки с документами
    if not Path(DATA_DIR).exists():
        os.makedirs(DATA_DIR)
        st.error(f"Создана папка {DATA_DIR}. Добавьте DOCX-файлы и перезапустите приложение!")
        st.stop()

    if not list(Path(DATA_DIR).glob("*.docx")):
        st.error(f"В папке {DATA_DIR} нет DOCX-файлов!")
        st.stop()

    # Проверка модели эмбеддингов
    if not Path(MODEL_DIR).exists():
        st.error(f"Модель эмбеддингов не найдена в {MODEL_DIR}!")
        st.stop()

    # Загрузка документов
    with st.spinner("Обработка документов..."):
        texts = process_folder(DATA_DIR)
        if not texts:
            st.error("Не удалось извлечь текст из документов!")
            st.stop()

    # Инициализация векторного хранилища (Postgres + pgvector)
    with st.spinner("Инициализация поисковой системы..."):
        vs = VectorStore(MODEL_DIR, DB_PARAMS)
        vs.create_index(texts)
        db = vs

    # Инициализация языковой модели
    with st.spinner("Загрузка языковой модели..."):
        llm = LLMConnector()

    return llm, db

# --- Интерфейс чата ---
def chat_interface(llm, db):
    """Основной интерфейс чата"""
    st.title("🤖 Локальный RAG-чат")
    st.caption(f"Документы из: {DATA_DIR} | Модель: Mistral 7B")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Отображение истории
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Обработка запроса
    if prompt := st.chat_input("Ваш вопрос по документам"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                # Поиск контекста
                docs = db.similarity_search(prompt, k=3)

                # st.subheader("🔎 Извлечённый контекст из FAISS:")
                # for i, d in enumerate(docs, 1):
                #     st.write(f"Источник {i}:")
                #     st.code(d['page_content'][:1000])

                context = "\n\n".join([f"📄 {d['page_content']}" for d in docs])
                
                # Генерация ответа
                message_placeholder = st.empty()
                full_response = ""
                
                for chunk in llm.generate_response(prompt, context):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Ошибка обработки запроса: {str(e)}")
                raise  # Добавлено для отладки
            
# --- Основной поток ---
def main():
    st.set_page_config(page_title="Локальный RAG-чат", layout="wide")
    
    with st.container():
        st.write("## Инициализация системы...")
        llm, db = initialize_system()
        st.success("✅ Система готова к работе!")
        
    chat_interface(llm, db)

if __name__ == "__main__":
    main()

