from PyPDF2 import PdfReader
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
        chunks.append(text[start:end]) # append 1 chunk with index [start:end]
        start += chunk_size - overlap
    return chunks
    

def process_pdf(file_path):
    """Извлекает текст из файлов и режет на чанки"""
    file = PdfReader(file_path)
    full_text = "\n".join([page.extract_text() or "" for page in file.pages])
    return [
        {
            "page_content": chunk,
            "metadata": {
                "source": file_path.name,
                "type_document": "pdf"
            },
        }
        for chunk in chunk_text(full_text) if chunk.strip()
    ]
    

def process_pdf_folder(folder_path: str):
    """Обрабатываем папку с файлами PDF"""
    folder = Path(folder_path)
    texts = []
    for file in folder.glob("*.pdf"):
        texts.extend(process_pdf(file))
    return texts