import os
import json
import subprocess
import shutil
import tempfile
from urllib.parse import urlparse
from core.llm import generate_ai_response


def normalize_github_repo_url(repo_url):
    """Validate a public GitHub repository URL and return its canonical HTTPS URL/name."""
    candidate = (repo_url or '').strip()
    if candidate.startswith('git@github.com:'):
        candidate = 'https://github.com/' + candidate.split(':', 1)[1]
    parsed = urlparse(candidate)
    if parsed.scheme not in ('http', 'https') or parsed.netloc.lower() not in ('github.com', 'www.github.com'):
        raise ValueError('Paste a public GitHub repository URL, for example https://github.com/owner/repository.')
    parts = [part for part in parsed.path.split('/') if part]
    if len(parts) != 2:
        raise ValueError('Paste the repository URL only (https://github.com/owner/repository), not a file or branch link.')
    owner, repository = parts
    if repository.endswith('.git'):
        repository = repository[:-4]
    if not owner or not repository:
        raise ValueError('The GitHub repository URL is incomplete.')
    return f'https://github.com/{owner}/{repository}', f'{owner}/{repository}'

def clone_repo(repo_url):
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"DEBUG: Cloning {repo_url} into {temp_dir}")
        subprocess.run(
            ['git', 'clone', '--depth', '1', '--single-branch', repo_url, temp_dir],
            check=True,
            capture_output=True,
            timeout=120,
        )
        if os.path.exists(temp_dir) and len(os.listdir(temp_dir)) > 0:
            print("DEBUG: Clone successful and verified non-empty.")
            return temp_dir
        else:
            print("DEBUG: Clone produced empty directory.")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"DEBUG: Clone failed with error: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

def build_file_tree(repo_path):
    tree = {}
    file_count = 0
    total_size = 0
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')
        
        rel_root = os.path.relpath(root, repo_path)
        if rel_root == '.':
            current = tree
        else:
            parts = rel_root.split(os.sep)
            current = tree
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        for file in files:
            current[file] = None
            file_count += 1
            total_size += os.path.getsize(os.path.join(root, file))
            
    return tree, file_count, total_size

def detect_tech_stack(repo_path):
    stack = []
    has_py = False
    has_js = False
    has_ts = False
    has_java = False
    has_go = False
    has_rb = False
    has_php = False
    has_html = False
    has_css = False
    has_rust = False
    has_package_json = False
    has_requirements = False
    has_manage_py = False
    has_gemfile = False
    has_composer = False
    
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')
        for file in files:
            name_lower = file.lower()
            if name_lower.endswith('.py'):
                has_py = True
            elif name_lower.endswith('.js') or name_lower.endswith('.jsx'):
                has_js = True
            elif name_lower.endswith('.ts') or name_lower.endswith('.tsx'):
                has_ts = True
            elif name_lower.endswith('.java'):
                has_java = True
            elif name_lower.endswith('.go'):
                has_go = True
            elif name_lower.endswith('.rb'):
                has_rb = True
            elif name_lower.endswith('.php'):
                has_php = True
            elif name_lower.endswith('.html'):
                has_html = True
            elif name_lower.endswith('.css'):
                has_css = True
            elif name_lower.endswith('.rs'):
                has_rust = True
                
            if name_lower == 'package.json':
                has_package_json = True
            elif name_lower == 'requirements.txt':
                has_requirements = True
            elif name_lower == 'manage.py':
                has_manage_py = True
            elif name_lower == 'gemfile':
                has_gemfile = True
            elif name_lower == 'composer.json':
                has_composer = True
    
    if has_manage_py:
        stack.append("Django")
    elif has_py:
        stack.append("Python")
        
    if has_package_json:
        stack.append("Node.js")
    elif has_js or has_ts:
        stack.append("JavaScript/TypeScript")
        
    if has_java:
        stack.append("Java")
    if has_go:
        stack.append("Go")
    if has_rb:
        stack.append("Ruby")
    if has_php:
        stack.append("PHP")
    if has_rust:
        stack.append("Rust")
    if has_html:
        stack.append("HTML")
    if has_css:
        stack.append("CSS")
        
    if not stack:
        stack = ["Unknown/Other"]
    return stack

def collect_sample_files(repo_path, max_files=10, max_size=50000):
    collected_text = ""
    files_collected = 0
    
    # Priority files list
    priority_names = ['readme.md', 'readme', 'package.json', 'requirements.txt', 'cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'composer.json']
    
    # Step 1: Scan for priority files
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')
        for file in files:
            if file.lower() in priority_names:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        rel_path = os.path.relpath(file_path, repo_path)
                        collected_text += f"\n--- {rel_path} ---\n{content[:2000]}\n"
                        files_collected += 1
                        if files_collected >= max_files or len(collected_text) > max_size:
                            break
                except Exception:
                    pass
        if files_collected >= max_files or len(collected_text) > max_size:
            break
            
    # Step 2: Fallback scan if we found less than 200 characters of priority files
    if len(collected_text.strip()) < 200:
        collected_text = ""
        files_collected = 0
        extensions = ('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php', '.html', '.css')
        for root, dirs, files in os.walk(repo_path):
            if '.git' in dirs:
                dirs.remove('.git')
            for file in files:
                if file.lower().endswith(extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            rel_path = os.path.relpath(file_path, repo_path)
                            collected_text += f"\n--- {rel_path} ---\n{content[:2000]}\n"
                            files_collected += 1
                            if files_collected >= 5 or len(collected_text) > max_size:
                                break
                    except Exception:
                        pass
            if files_collected >= 5 or len(collected_text) > max_size:
                break
                
    return collected_text

def generate_codebase_summary(file_tree, sample_files):
    """Generate summary using Hugging Face Inference API (FREE)."""
    prompt = f"""Below is a file tree and sample file contents from a real repository. Base your summary strictly and only on what is shown below. If the content is insufficient to determine the project's real purpose or structure, say so plainly instead of guessing. Never describe files, frameworks, or architecture that are not directly evidenced in the content provided to you.

Write a clear repository summary formatted like an engineer briefing a teammate:
1. What the project does (brief explanation).
2. Its real detected tech stack.
3. Its actual structure based on what was found.

Do not invent details.

FORMAT YOUR RESPONSE USING MARKDOWN:
- Use proper line breaks between sections
- Use headers (# ## ###) to organize sections clearly
- Use **bold** for emphasis on key technologies
- Use bullet points for lists
- Keep paragraphs short and readable
- Structure for clarity, not density

File Tree:
{json.dumps(file_tree, indent=2)[:5000]}

Sample Files:
{sample_files[:15000]}

Summary:"""

    response = generate_ai_response(prompt, max_tokens=800)
    return response

def process_new_repo(repo_url):
    repo_path = clone_repo(repo_url)
    if not repo_path or not os.path.exists(repo_path) or len(os.listdir(repo_path)) == 0:
        if repo_path:
            shutil.rmtree(repo_path, ignore_errors=True)
        raise ValueError("Could not clone this repository — it may be private, deleted, or the URL is incorrect.")

    try:
        file_tree, file_count, total_size = build_file_tree(repo_path)
        print(f"DEBUG: build_file_tree returned {file_count} files.")
        
        tech_stack = detect_tech_stack(repo_path)
        
        if file_count == 0:
            print("DEBUG: Zero files found in repo. Skipping Gemini.")
            return {
                'file_tree': file_tree,
                'file_count': file_count,
                'total_size': total_size,
                'tech_stack': ["Empty"],
                'ai_summary': "This repository appears to be empty or contains no recognizable source files.",
                'sample_files': "",
                'status': 'ready',
                'repo_path': repo_path
            }

        sample_files = collect_sample_files(repo_path)
        print(f"DEBUG: collect_sample_files returned {len(sample_files)} characters.")
        
        if len(sample_files.strip()) < 200:
            print("DEBUG: Sample files < 200 chars. Skipping Gemini.")
            return {
                'file_tree': file_tree,
                'file_count': file_count,
                'total_size': total_size,
                'tech_stack': tech_stack,
                'ai_summary': "This repository appears to be empty or contains no recognizable source files.",
                'sample_files': sample_files,
                'status': 'ready',
                'repo_path': repo_path
            }

        ai_summary = generate_codebase_summary(file_tree, sample_files)

        return {
            'file_tree': file_tree,
            'file_count': file_count,
            'total_size': total_size,
            'tech_stack': tech_stack,
            'ai_summary': ai_summary,
            'sample_files': sample_files,
            'status': 'ready',
            'repo_path': repo_path
        }
    except Exception as e:
        shutil.rmtree(repo_path, ignore_errors=True)
        raise e
