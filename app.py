import streamlit as st
from llm_connector import LLMConnector
from vector_store_pg import VectorStore
from config import EMBEDDING_PATH, DB_PARAMS
from pathlib import Path
import os


def initialize_system():
    """Инициализация всех компонентов с проверками"""

    if not Path(EMBEDDING_PATH).exists():
        st.error(f"Модель эмбеддингов не найдена в {EMBEDDING_PATH}!")
        st.stop()

    with st.spinner("Инициализация поисковой системы..."):
        db = VectorStore(EMBEDDING_PATH, DB_PARAMS)

    with st.spinner("Загрузка языковой модели..."):
        llm = LLMConnector()

    return llm, db

def chat_interface(llm, db):
    """Основной интерфейс чата"""
    st.title("🤖 Локальный RAG-чат")
    st.caption(f"Модель: Mistral 7B")

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
                docs = db.hybrid_search(prompt)

                # st.subheader("🔎 Извлечённый контекст из FAISS:")
                # for i, d in enumerate(docs, 1):
                #     st.write(f"Источник {i}:")
                #     st.code(d['page_content'][:1000])

                context = "\n\n".join([
                    f'📄 [{d["metadata"]["type_document"].upper()} | {d["metadata"]["source"]}]\n{d["page_content"]}' 
                    for d in docs
                ])
                
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
            
def main():
    st.set_page_config(page_title="Локальный RAG-чат", layout="wide")
    
    with st.container():
        st.write("## Инициализация системы...")
        llm, db = initialize_system()
        st.success("✅ Система готова к работе!")
        
    chat_interface(llm, db)

if __name__ == "__main__":
    main()