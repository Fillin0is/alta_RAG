from openai import OpenAI
import time
from config import API_KEY, BASE_URL, CHAT_MODEL, EMBED_MODEL

class LLMConnector:
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.model = CHAT_MODEL

    def generate_response(self, query, context):
        """
        Генерация ответа через API, потоково
        """
        augmented_prompt = f'''
        Ты - ассистент компании Альта-Софт, которая занимается разработкой программного обеспечения в сфере таможенного оборота и логистики. 
        Твоя задача отвечать на вопрос, используя приведенный нижже контекст.
        Если ответа в контексте нет или вопрос имеет несколько интерпретаций, то либо попроси уточнить вопрос, либо не отвечай на него, чтобы не дезинформаировать клиента.

        Контекст: {context}

        Вопрос: {query}

        Ответ:
        '''

        '''
        with self.client.chat.completions.stream(
            model=self.model,
            messages=[
                {"role": "system", "content": "Ты умный ассистент, отвечай строго по контексту."},
                {"role": "user", "content": augmented_prompt}
            ],
            max_tokens=1024,
            temperature=0.5,
        ) as stream:
            for event in stream:
                if event.type == "message.delta" and event.delta.content:
                    print(event.delta.content, end='', flush=True)
                    yield event.delta.content
                    time.sleep(0.2)
        '''

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Ты умный ассистент, отвечай строго по контексту."},
                {"role": "user", "content": augmented_prompt}
            ],
            stream=True,
            max_tokens=1024,
            temperature=0.5
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                time.sleep(0.02)


class EmbedConnector:
    """
    Универсальный я API эмбеддер.
    Используется для генерации эмбеддингов в Retriever
    """
    def __init__(self):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.model = EMBED_MODEL

    def embed_text(self, text: str):
        res = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return res.data[0].embedding
    
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Батчевое получение эмбеддингов"""
        if isinstance(texts, str):
            texts = [texts]
        res = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [d.embedding for d in res.data]