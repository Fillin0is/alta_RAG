from docx import Document
from pathlib import Path


def chunk_text(text: str, chunk_size: int = 700, overlap: int = 200):
    """
    Разбиваем длинный текст на мелкие куски фиксированной длины.
    overlap = перекрытие, чтобы не терялся смысл между чанками.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap
    return chunks

def process_docx(file_path: Path):
    """
    Извлекает текст из файлов и режет на чанки
    """
    doc = Document(file_path)
    full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return [
        {"page_content": chunk, "metadata": {"source": file_path.name}}
        for chunk in chunk_text(full_text)
        if chunk.strip()
    ]

def process_docx_folder(folder_path: str):
    """Обрабатываем папку с файлами DOCX"""
    folder = Path(folder_path)
    texts = []
    for file in folder.glob("*.docx"):
        texts.extend(process_docx(file))
    return texts