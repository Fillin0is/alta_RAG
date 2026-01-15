import streamlit as st

import requests


API_URL = "http://api:8000"

def check_api_health():
    response = requests.get(f"{API_URL}/health")
    if response.status_code != 200:
        st.error("API error")
        return False
    return True

def send_message(query: str):
    response = requests.get(f"{API_URL}/generate", params={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Ошибка API {response.status_code}"}

def main():
    st.set_page_config(page_title="Альта-RAG", layout="wide")

    if not check_api_health():
        st.stop()

    st.title("Альта-RAG")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if query := st.chat_input("Введите запрос:"):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            result = send_message(query)

            if "error" in result:
                st.error(result["error"])
            else:
                answer = result.get("answer", "Нет ответа")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

if __name__ == "__main__":
    main()