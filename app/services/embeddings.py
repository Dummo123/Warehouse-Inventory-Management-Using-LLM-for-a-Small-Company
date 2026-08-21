from __future__ import annotations

from typing import Optional

import numpy as np

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def embed(texts: list[str]) -> np.ndarray:
    model = _get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")


def _cosine_topk(index_vecs: np.ndarray, query_vec: np.ndarray) -> tuple[int, float]:
    sims = index_vecs @ query_vec
    best_idx = int(np.argmax(sims))
    return best_idx, float(sims[best_idx])


CANONICAL_QUESTIONS = {
    "production_shortage": "Чего не хватает на складе для производства артикула в заданном количестве?",
    "purchase_plan": "Что нужно закупить в этом месяце исходя из остатков и динамики расхода?",
    "top_sellers": "Какие товары продавались лучше всего за прошлый месяц?",
    "revenue_by_channel": "Сколько было продано на рубли по артикулу за прошлый квартал по каналам продаж?",
    "available_funds": "Какая сумма доступна для развития и дивидендов за прошлый месяц?",
}

_canonical_index: Optional[np.ndarray] = None
_canonical_keys: list[str] = []


def _ensure_canonical_index():
    global _canonical_index, _canonical_keys
    if _canonical_index is None:
        _canonical_keys = list(CANONICAL_QUESTIONS.keys())
        _canonical_index = embed(list(CANONICAL_QUESTIONS.values()))


def classify_intent(question: str, threshold: float = 0.45) -> Optional[str]:
    _ensure_canonical_index()
    q_vec = embed([question])[0]
    best_idx, score = _cosine_topk(_canonical_index, q_vec)
    if score < threshold:
        return None
    return _canonical_keys[best_idx]


def find_article_by_name(db, query_text: str, article_type=None, threshold: float = 0.35):
    from app.models.models import Article

    q = db.query(Article).filter(Article.is_active == True)
    if article_type is not None:
        q = q.filter(Article.article_type == article_type)
    articles = q.all()
    if not articles:
        return None

    names = [f"{a.code} {a.name}" for a in articles]
    name_vecs = embed(names)
    q_vec = embed([query_text])[0]
    best_idx, score = _cosine_topk(name_vecs, q_vec)
    if score < threshold:
        return None
    return articles[best_idx]