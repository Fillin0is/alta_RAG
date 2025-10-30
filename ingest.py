from config import DB_PARAMS, DOCX_PATH, OBSIDIAN_PATH, EMBEDDING_PATH, PDF_PATH
from vector_store_pg import VectorStore
from parsers.docx_parser import process_docx_folder
from parsers.obsidian_parser import process_obsidian_folder
from parsers.pdf_parser import process_pdf_folder


def main() -> None:
    store = VectorStore(embed_path=EMBEDDING_PATH, db_params=DB_PARAMS)

    documents = []
    """
    Обработанные документы в формате
    [([{'page_content': 'text_chunk', 'metadata': {'source': 'file_name', 'type_document': '...'}}, ...], relative_file_path), ...]
    """
    docx_processed_files = process_docx_folder(DOCX_PATH)
    obsidian_processed_files = process_obsidian_folder(OBSIDIAN_PATH)
    pdf_processed_files = process_pdf_folder(PDF_PATH)

    print(f"Индексировано {sum([len(file[0]) for file in docx_processed_files])} чанков формата .docx")
    print(f"Индексировано {sum([len(file[0]) for file in obsidian_processed_files])} чанков формата .md")
    print(f"Индексировано {sum([len(file[0]) for file in pdf_processed_files])} чанков формата .pdf")

    documents.extend(docx_processed_files)
    documents.extend(obsidian_processed_files)
    documents.extend(pdf_processed_files)

    for document in documents:
        store.create_index(document[0], document[1])

    print("-- Индексация документов окончена --")


if __name__ == "__main__":
    main()