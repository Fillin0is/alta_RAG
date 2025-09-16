from config import DB_PARAMS, DOCX_PATH, OBSIDIAN_PATH, EMBEDDING_PATH, PDF_PATH
from vector_store_pg import VectorStore
from parsers.docx_parser import process_docx_folder
from parsers.obsidian_parser import process_obsidian_folder
from parsers.pdf_parser import process_pdf_folder


def main():
    store = VectorStore(embed_path=EMBEDDING_PATH, db_params=DB_PARAMS)

    texts = []
    docx_chunks = process_docx_folder(DOCX_PATH)
    obsidian_chunks = process_obsidian_folder(OBSIDIAN_PATH)
    pdf_chunks = process_pdf_folder(PDF_PATH)

    print(f"Индексировано {len(docx_chunks)} чанков формата .docx")
    print(f"Индексировано {len(obsidian_chunks)} чанков формата .md")
    print(f"ИНдексировано {len(pdf_chunks)} чанков формата .pdf")

    texts.extend(docx_chunks)
    texts.extend(obsidian_chunks)
    texts.extend(pdf_chunks)

    store.create_index(texts)


if __name__ == "__main__":
    main()