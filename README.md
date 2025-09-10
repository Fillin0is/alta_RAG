# 🧠 RAG System with PostgreSQL + pgvector

Локальный RAG-чат, который:
- обрабатывает `.docx`, `.md` документы,
- индексирует их эмбеддинги в PostgreSQL (pgvector),
- отвечает на вопросы через LLM.

## 🚀 Запуск

```bash
git clone https://github.com/<ТВОЙ_НИК>/<РЕПО>
cd <РЕПО>
python -m venv venv
source venv/bin/activate  # или venv\Scripts\activate на Windows
pip install -r requirements.txt
streamlit run app.py
