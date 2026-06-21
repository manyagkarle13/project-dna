import numpy as np

# Global model cache to load model lazily
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def embed_texts(texts):
    if not texts:
        return []
    model = get_embedding_model()
    embeddings = model.encode(texts)
    return embeddings.tolist()

def embed_query(query):
    model = get_embedding_model()
    embedding = model.encode(query)
    return embedding.tolist()

def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
