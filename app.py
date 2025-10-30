import streamlit as st
from llm_connector import LLMConnector, EmbedConnector
from vector_store_pg import VectorStore
from retriever import AnswerSearch
from config import DB_PARAMS, params_config


def initialize_system():
    with st.spinner("Инициализация компонентов..."):
        db = VectorStore(params_config.embedders.embedding_3_small, DB_PARAMS)
        llm = LLMConnector()
        embedder = EmbedConnector()
        retriever = AnswerSearch(db.conn, embedder)
    return llm, retriever


def chat_interface(llm, retriever):
    st.title("🤖 Альта-чат")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Введите вопрос..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                docs = retriever.hybrid_search(prompt)
                context = "\n\n".join([
                    f"[{d['metadata'].get('source', 'Неизв.')}] {d['page_content']}" for d in docs
                ])
                message_placeholder = st.empty()
                full_response = ""

                response = llm.generate_response(prompt, context)

                # Проверяем, стримится ли ответ
                if hasattr(response, "__iter__") and not isinstance(response, str):
                    for chunk in response:
                        full_response += chunk or ""
                        message_placeholder.markdown(full_response + "▌")
                    message_placeholder.markdown(full_response)
                else:
                    # если возвращает обычную строку
                    message_placeholder.markdown(response)

                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Ошибка: {e}")


def main():
    st.set_page_config(page_title="RAG API", layout="wide")
    llm, retriever = initialize_system()
    chat_interface(llm, retriever)


if __name__ == "__main__":
    main()