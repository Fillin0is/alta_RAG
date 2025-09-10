from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer

# Скачиваем эмбеддинг-модель
snapshot_download(
    repo_id="sentence-transformers/all-mpnet-base-v2",
    local_dir="./models/all-mpnet-base-v2",
    local_dir_use_symlinks=False
)

# Тестовая загрузка
model = SentenceTransformer('./models/all-mpnet-base-v2')