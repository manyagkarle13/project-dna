import os

def chunk_repo_files(repo_root_path):
    chunks = []
    extensions = ('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php', '.html', '.css', '.md', '.json', '.yml', '.yaml')
    named_text_files = {'readme', 'license', 'makefile', 'dockerfile', 'gemfile', 'procfile'}
    ignored_dirs = {'.git', 'node_modules', 'venv', '.venv', 'dist', 'build', '__pycache__'}
    
    for root, dirs, files in os.walk(repo_root_path):
        dirs[:] = [directory for directory in dirs if directory not in ignored_dirs]
        
        for file in files:
            if file.lower().endswith(extensions) or file.lower() in named_text_files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    rel_path = os.path.relpath(file_path, repo_root_path)
                    
                    chunk_size = 400
                    overlap = 50
                    
                    if not lines:
                        continue
                        
                    idx = 0
                    start = 0
                    while start < len(lines):
                        end = min(start + chunk_size, len(lines))
                        chunk_content = "".join(lines[start:end])
                        chunks.append({
                            'file_path': rel_path,
                            'chunk_index': idx,
                            'content': chunk_content
                        })
                        idx += 1
                        if end == len(lines):
                            break
                        start += (chunk_size - overlap)
                        
                except Exception:
                    pass
    return chunks
