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
    import numpy as np
    query_embedding = embed_query(query)
    
    chunks = list(CodeChunk.objects.filter(repo=connected_repo))
    if not chunks:
        return []
        
    query_vector = np.array(query_embedding)
    
    def get_similarity(chunk):
        chunk_vector = np.array(chunk.embedding)
        norm_chunk = np.linalg.norm(chunk_vector)
        norm_query = np.linalg.norm(query_vector)
        if norm_chunk == 0 or norm_query == 0:
            return 0.0
        return np.dot(chunk_vector, query_vector) / (norm_chunk * norm_query)

    chunks.sort(key=get_similarity, reverse=True)
    return chunks[:top_k]
