from sentence_transformers import SentenceTransformer
import numpy as np

# Load model locally once at module level
model = SentenceTransformer('all-MiniLM-L6-v2')

def embed_texts(texts):
    if not texts:
        return []
    embeddings = model.encode(texts)
    return embeddings.tolist()

def embed_query(query):
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
