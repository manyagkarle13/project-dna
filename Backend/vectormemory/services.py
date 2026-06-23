from vectormemory.models import CodeChunk
from vectormemory.chunking import chunk_repo_files
from vectormemory.embeddings import embed_texts, embed_query

def index_repo(connected_repo, repo_local_path):
    chunks = chunk_repo_files(repo_local_path)
    if not chunks:
        return 0
        
    texts = [c['content'] for c in chunks]
    embeddings = embed_texts(texts)
    
    CodeChunk.objects.filter(repo=connected_repo).delete()
    
    code_chunks = []
    for chunk, emb in zip(chunks, embeddings):
        code_chunks.append(
            CodeChunk(
                repo=connected_repo,
                file_path=chunk['file_path'],
                chunk_index=chunk['chunk_index'],
                content=chunk['content'],
                embedding=emb
            )
        )
        
    CodeChunk.objects.bulk_create(code_chunks)
    print(f"Indexed {len(code_chunks)} chunks for repo {connected_repo.full_name}")
    return len(code_chunks)

def search_relevant_chunks(connected_repo, query, top_k=5):
    from vectormemory.embeddings import get_use_fallback
    
    chunks = list(CodeChunk.objects.filter(repo=connected_repo))
    if not chunks:
        return []

    # If the vector model failed to load, fall back to keyword term frequency search
    if get_use_fallback():
        import re
        query_words = [w.lower() for w in re.findall(r'\b\w+\b', query) if len(w) > 1]
        if not query_words:
            return chunks[:top_k]
            
        def get_keyword_score(chunk):
            score = 0
            content_lower = chunk.content.lower()
            file_path_lower = chunk.file_path.lower()
            for word in query_words:
                count = content_lower.count(word)
                score += count
                # Boost files whose name contains the search word
                if word in file_path_lower:
                    score += 10
            return score
            
        chunks.sort(key=get_keyword_score, reverse=True)
        return chunks[:top_k]

    # Standard vector-based cosine similarity search
    import numpy as np
    try:
        query_embedding = embed_query(query)
        if not query_embedding:
            # Fallback if query embedding returned empty list
            raise ValueError("Empty query embedding")
        query_vector = np.array(query_embedding)
        
        def get_similarity(chunk):
            if not chunk.embedding:
                return 0.0
            chunk_vector = np.array(chunk.embedding)
            norm_chunk = np.linalg.norm(chunk_vector)
            norm_query = np.linalg.norm(query_vector)
            if norm_chunk == 0 or norm_query == 0:
                return 0.0
            return np.dot(chunk_vector, query_vector) / (norm_chunk * norm_query)

        chunks.sort(key=get_similarity, reverse=True)
        return chunks[:top_k]
    except Exception as e:
        print(f"Warning: Vector search error: {e}. Falling back to keyword search.")
        import re
        query_words = [w.lower() for w in re.findall(r'\b\w+\b', query) if len(w) > 1]
        if not query_words:
            return chunks[:top_k]
            
        def get_keyword_score(chunk):
            score = 0
            content_lower = chunk.content.lower()
            file_path_lower = chunk.file_path.lower()
            for word in query_words:
                score += content_lower.count(word)
                if word in file_path_lower:
                    score += 10
            return score
            
        chunks.sort(key=get_keyword_score, reverse=True)
        return chunks[:top_k]
