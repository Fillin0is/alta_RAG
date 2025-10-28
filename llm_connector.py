from llama_cpp import Llama
from config import MODEL_PATH, N_CTX, N_TREADS, N_GPU_LAYERS


class LLMConnector:
    def __init__(self):
        self.llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_TREADS,
            n_gpu_layers=N_GPU_LAYERS,
            verbose=False,
        )

    def generate_response(self, prompt, context, max_tokens=512):
        """Генерация ответа с использованием контекста"""
        augmented_prompt = f'''
        Ты - ассистент компании Альта-Софт, которая занимается разработкой программного обеспечения в сфере таможенного оборота и логистики. 
        Твоя задача отвечать на вопрос, используя приведенный нижже контекст.
        Если ответа в контексте нет или вопрос имеет несколько интерпретаций, то либо попроси уточнить вопрос, либо не отвечай на него, чтобы не дезинформаировать клиента.

        Контекст: {context}

        Вопрос: {prompt}

        Ответ:
        '''

        try:
            response = self.llm.create_chat_completion(
                messages=[
                    {"role": "system", "content": "Ты полезный корпоративный ассистент."},
                    {"role": "user", "content": augmented_prompt},
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in response:
                yield chunk["choices"][0]["delta"].get("content", "")

        except Exception as e:
            yield f"⚠️ Ошибка генерации: {str(e)}"