import os
import time
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings

os.environ["HF_HOME"] = "D:/huggingface_cache"

class HuggingFaceClient:
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        self.model_name = model_name
        self.emb = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={},  # CPU
            encode_kwargs={"normalize_embeddings": True}
        )
        print(f"[Embed] model={self.model_name} (CPU)")

    def embed(self, text: str) -> List[float]:
        return self.emb.embed_query(text)

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return self.emb.embed_documents(texts)

if __name__ == "__main__":
    # ✅ 데모/테스트 코드는 전부 여기 안으로
    client = HuggingFaceClient()
    start = time.time()
    emb = client.embed("하이 매번 계속수정수정 반복임.")
    print(emb[:10])
    print(f"처리 시간: {time.time() - start:.2f}초")

    import numpy as np
    def cos(a, b):
        a = np.array(a); b = np.array(b)
        return float(np.dot(a, b) / (np.linalg.norm(a)*np.linalg.norm(b) + 1e-12))

    pairs = [
        ("보온병", "텀블러"),
        ("보온병", "머그컵"),
        ("보온병", "비행기"),
        ("동료갈등", "직장갈등"),
    ]
    tokens = {x for p in pairs for x in p}
    vecs = {t: client.embed(t) for t in tokens}
    for a, b in pairs:
        print(a, "~", b, "=", round(cos(vecs[a], vecs[b]), 3))
