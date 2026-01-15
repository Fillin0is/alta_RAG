from pathlib import Path
import re


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
    return [c for c in chunks if c]

def process_md(file: object, folder_path: Path):
    """
    Извлекаем текст из Obsidian (markdown) файла и режем на чанки
    """
    text = file.read_text(encoding="utf-8")

    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = text.replace('  ', '')
    text = text.replace('--', '')

    return ([
        {
            "page_content": chunk, 
            "metadata": {
                "source": str(file), 
                "type_document": "md"
            }
        }
        for chunk in chunk_text(text)
        if chunk.strip()
    ], str(file))

def process_obsidian_folder(folder_path: str):
    """Обрабатываем папку с Obsidian файлами"""
    folder = Path(folder_path)
    texts = []
    for file in folder.rglob("*.md"):
        texts.append(process_md(file, folder_path))
    return texts