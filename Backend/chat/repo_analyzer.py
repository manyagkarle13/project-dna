"""
Git link analyzer - auto-analyze, fix bugs, and prepare deployment for any repo
"""
import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

class RepoAnalyzer:
    """Analyze external git repos, detect bugs, and prepare fixes"""

    def __init__(self, git_url: str):
        self.git_url = git_url
        self.repo_name = git_url.split('/')[-1].replace('.git', '')
        self.temp_dir = None
        self.analysis = {
            'repo_name': self.repo_name,
            'git_url': git_url,
            'tech_stack': [],
            'deployment_issues': [],
            'bugs_found': [],
            'fixes_suggested': [],
            'fixes_detailed': {},
            'summary': '',
            'file_tree': {}
        }

    def clone_repo(self) -> bool:
        """Clone repo to temp directory"""
        try:
            self.temp_dir = tempfile.mkdtemp()
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', self.git_url, self.temp_dir],
                capture_output=True,
                timeout=60
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Clone error: {e}")
            return False

    def cleanup(self):
        """Clean up temp directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def detect_tech_stack(self) -> List[str]:
        """Detect technology stack from files"""
        stack = []
        indicators = {
            'Python': ['requirements.txt', 'setup.py', 'Pipfile'],
            'Node.js': ['package.json'],
            'JavaScript': ['package.json'],
            'React': ['package.json'],
            'Django': ['manage.py'],
            'Docker': ['Dockerfile'],
            'PostgreSQL': ['docker-compose.yml'],
        }

        for tech, files in indicators.items():
            for f in files:
                if os.path.exists(os.path.join(self.temp_dir, f)):
                    if tech not in stack:
                        stack.append(tech)

        self.analysis['tech_stack'] = stack
        return stack

    def scan_for_bugs(self) -> List[Dict]:
        """Scan for common bugs and deployment issues"""
        bugs = []

        # Check Dockerfile issues
        dockerfile = os.path.join(self.temp_dir, 'Dockerfile')
        if os.path.exists(dockerfile):
            with open(dockerfile, 'r') as f:
                content = f.read()

                # Check for hardcoded ports
                if ':8000' in content or ':5000' in content or ':3000' in content:
                    bugs.append({
                        'type': 'deployment',
                        'severity': 'high',
                        'file': 'Dockerfile',
                        'line': None,
                        'issue': 'Hardcoded port detected - use $PORT for cloud deployment (Render, Railway)',
                        'fix_type': 'dynamic_port'
                    })

                # Check for exec form CMD without expansion
                if 'CMD ["' in content and '$' not in content:
                    bugs.append({
                        'type': 'deployment',
                        'severity': 'high',
                        'file': 'Dockerfile',
                        'line': None,
                        'issue': 'Exec form CMD blocks environment variable expansion',
                        'fix_type': 'shell_form_cmd'
                    })

        # Check for missing migrations in Django
        if 'Django' in self.analysis['tech_stack']:
            manage_py = os.path.join(self.temp_dir, 'manage.py')
            dockerfile = os.path.join(self.temp_dir, 'Dockerfile')
            if os.path.exists(manage_py) and os.path.exists(dockerfile):
                with open(dockerfile, 'r') as f:
                    docker_content = f.read()
                    if 'migrate' not in docker_content:
                        bugs.append({
                            'type': 'deployment',
                            'severity': 'high',
                            'file': 'Dockerfile',
                            'line': None,
                            'issue': 'Migrations not run on container startup - database schema missing on deploy',
                            'fix_type': 'add_migrations'
                        })

        # Check requirements.txt
        req_file = os.path.join(self.temp_dir, 'requirements.txt')
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                reqs = f.read()
                if 'Django' in self.analysis['tech_stack'] and 'gunicorn' not in reqs:
                    bugs.append({
                        'type': 'deployment',
                        'severity': 'high',
                        'file': 'requirements.txt',
                        'line': None,
                        'issue': 'gunicorn not in requirements - production needs WSGI server',
                        'fix_type': 'add_gunicorn'
                    })

        self.analysis['bugs_found'] = bugs
        return bugs

    def generate_fixes(self) -> Dict:
        """Generate fixes for detected bugs"""
        fixes = {}

        for bug in self.analysis['bugs_found']:
            if bug['fix_type'] == 'dynamic_port':
                fixes['dynamic_port'] = self._fix_dynamic_port()
            elif bug['fix_type'] == 'shell_form_cmd':
                fixes['shell_form_cmd'] = self._fix_shell_form_cmd()
            elif bug['fix_type'] == 'add_migrations':
                fixes['add_migrations'] = self._fix_add_migrations()
            elif bug['fix_type'] == 'add_gunicorn':
                fixes['add_gunicorn'] = self._fix_add_gunicorn()

        self.analysis['fixes_detailed'] = fixes
        self.analysis['fixes_suggested'] = list(fixes.keys())
        return fixes

    def _fix_dynamic_port(self) -> Dict:
        return {
            'type': 'dynamic_port',
            'description': 'Use environment variable $PORT instead of hardcoded port',
            'steps': [
                'Replace hardcoded port (e.g., 0.0.0.0:8000) with 0.0.0.0:$PORT',
                'Change CMD from exec form to shell form',
                'Update EXPOSE or remove it'
            ],
            'example_change': {
                'before': 'CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app:app"]',
                'after': 'CMD gunicorn --bind 0.0.0.0:$PORT --workers 4 app:app'
            }
        }

    def _fix_shell_form_cmd(self) -> Dict:
        return {
            'type': 'shell_form_cmd',
            'description': 'Convert Dockerfile CMD to shell form for $PORT expansion',
            'steps': [
                'Remove JSON array brackets from CMD',
                'Example: CMD ["python", "app.py"] → CMD python app.py',
                'Now environment variables like $PORT will be expanded at runtime'
            ],
            'why': 'Exec form CMD does not expand environment variables. Shell form does.'
        }

    def _fix_add_migrations(self) -> Dict:
        return {
            'type': 'add_migrations',
            'description': 'Add entrypoint script to run migrations before app starts',
            'files_to_create': {
                'entrypoint.sh': '''#!/bin/bash
set -e
python manage.py migrate --noinput
exec gunicorn --bind 0.0.0.0:$PORT --workers 4 backend_project.wsgi:application'''
            },
            'dockerfile_changes': [
                '1. Add after copying code:',
                'COPY entrypoint.sh .',
                'RUN chmod +x entrypoint.sh',
                '',
                '2. Replace CMD with:',
                'CMD ./entrypoint.sh'
            ],
            'why': 'Ensures database migrations run every deploy, preventing schema errors on first deploy'
        }

    def _fix_add_gunicorn(self) -> Dict:
        return {
            'type': 'add_gunicorn',
            'description': 'Add gunicorn to production requirements',
            'file': 'requirements.txt',
            'add_line': 'gunicorn>=21.0',
            'why': 'Django development server is not suitable for production. gunicorn is the standard WSGI server for Django apps.'
        }

    def get_file_content(self, file_path: str) -> str:
        """Get content of a file in the repo"""
        full_path = os.path.join(self.temp_dir, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', errors='ignore') as f:
                    return f.read()
            except:
                return ""
        return ""

    def build_summary(self) -> str:
        """Build analysis summary"""
        summary = f"""## 🔍 {self.repo_name}

**URL:** `{self.git_url}`

**Tech Stack:** {', '.join(self.analysis['tech_stack']) or '❌ Not detected'}

**Status:** {'✅ No issues' if not self.analysis['bugs_found'] else f'⚠️ {len(self.analysis["bugs_found"])} issues found'}
"""

        if self.analysis['bugs_found']:
            summary += "\n### 🐛 Issues Found:\n\n"
            for i, bug in enumerate(self.analysis['bugs_found'], 1):
                severity_icon = '🔴' if bug['severity'] == 'high' else '🟡'
                summary += f"{i}. {severity_icon} **{bug['issue']}**\n"
                summary += f"   - File: `{bug['file']}`\n"
                summary += f"   - Severity: `{bug['severity'].upper()}`\n\n"

        summary += f"\n### 🔧 Fixes Applied: `{len(self.analysis['fixes_suggested'])}`\n"
        if self.analysis['fixes_suggested']:
            for fix in self.analysis['fixes_suggested']:
                summary += f"- ✅ {fix}\n"

        self.analysis['summary'] = summary
        return summary

    def analyze(self) -> Dict:
        """Run full analysis pipeline"""
        if not self.clone_repo():
            return {'error': 'Failed to clone repository. Check the URL.'}

        try:
            self.detect_tech_stack()
            self.scan_for_bugs()
            self.generate_fixes()
            self.build_summary()
            return self.analysis
        finally:
            self.cleanup()
