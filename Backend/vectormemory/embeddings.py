import numpy as np

# Global model cache to load model lazily
_model = None
_use_fallback = False

def get_embedding_model():
    global _model, _use_fallback
    if _use_fallback:
        return None
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Failed to load SentenceTransformer: {e}. Falling back to keyword-based search.")
            _use_fallback = True
            _model = None
    return _model

def get_use_fallback():
    global _use_fallback
    # Trigger model load to set the flag if not loaded yet
    if _model is None and not _use_fallback:
        get_embedding_model()
    return _use_fallback

def embed_texts(texts):
    if not texts:
        return []
    
    if get_use_fallback():
        return [[] for _ in texts]
        
    try:
        model = get_embedding_model()
        if model is None:
            return [[] for _ in texts]
        embeddings = model.encode(texts)
        return embeddings.tolist()
    except Exception as e:
        print(f"Warning: Error during embedding generation: {e}. Falling back to empty embeddings.")
        return [[] for _ in texts]

def embed_query(query):
    if get_use_fallback():
        return []
        
    try:
        model = get_embedding_model()
        if model is None:
            return []
        embedding = model.encode(query)
        return embedding.tolist()
    except Exception as e:
        print(f"Warning: Error during query embedding: {e}. Returning empty embedding.")
        return []

def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two vectors."""
    if not vec_a or not vec_b:
        return 0.0
    a = np.array(vec_a)
    b = np.array(vec_b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
