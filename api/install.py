from sentence_transformers import SentenceTransformer
from huggingface_hub import hf_hub_download

from config import EMBED_MODEL_PATH, LLM_MODEL_PATH


def install_embed_model():
    '''Download embedding model for vectorization query'''
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    model.save(str(EMBED_MODEL_PATH))
    print(f'Модель скачана в {str(EMBED_MODEL_PATH)}')

def install_LLM_model():
    '''Download LLM model for generate response for client'''
    hf_hub_download(
        repo_id="MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF",
        filename="Mistral-7B-Instruct-v0.3.Q8_0.gguf",
        local_dir="./models"
    )
    print(f'Модель скачана в {str(LLM_MODEL_PATH)}')

if __name__ == '__main__':
    install_embed_model()
    install_LLM_model()
