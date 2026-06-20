import subprocess
import os
import json

class BuildSystem:
    """Detect and run project build commands"""

    BUILD_SCRIPTS = {
        'npm': {
            'detect': 'package.json',
            'build': 'npm run build',
            'test': 'npm test',
            'lint': 'npm run lint',
            'install': 'npm install'
        },
        'yarn': {
            'detect': 'yarn.lock',
            'build': 'yarn build',
            'test': 'yarn test',
            'lint': 'yarn lint',
            'install': 'yarn install'
        },
        'pip': {
            'detect': 'requirements.txt',
            'build': 'pip install -r requirements.txt',
            'test': 'pytest',
            'lint': 'flake8',
            'install': 'pip install -r requirements.txt'
        },
        'poetry': {
            'detect': 'pyproject.toml',
            'build': 'poetry install',
            'test': 'poetry run pytest',
            'lint': 'poetry run flake8',
            'install': 'poetry install'
        },
        'cargo': {
            'detect': 'Cargo.toml',
            'build': 'cargo build',
            'test': 'cargo test',
            'lint': 'cargo clippy',
            'install': 'cargo build'
        },
        'maven': {
            'detect': 'pom.xml',
            'build': 'mvn clean package',
            'test': 'mvn test',
            'lint': 'mvn checkstyle:check',
            'install': 'mvn install'
        },
        'gradle': {
            'detect': 'build.gradle',
            'build': 'gradle build',
            'test': 'gradle test',
            'lint': 'gradle lint',
            'install': 'gradle build'
        },
        'make': {
            'detect': 'Makefile',
            'build': 'make build',
            'test': 'make test',
            'lint': 'make lint',
            'install': 'make install'
        }
    }

    @staticmethod
    def detect_build_system(repo_path):
        """Detect which build system is being used"""
        detected = []

        for system, config in BuildSystem.BUILD_SCRIPTS.items():
            detect_file = os.path.join(repo_path, config['detect'])
            if os.path.exists(detect_file):
                detected.append(system)

        return detected if detected else ['unknown']

    @staticmethod
    def get_build_command(repo_path):
        """Get the appropriate build command for the project"""
        systems = BuildSystem.detect_build_system(repo_path)

        if systems and systems[0] != 'unknown':
            system = systems[0]
            return {
                'system': system,
                'build': BuildSystem.BUILD_SCRIPTS[system].get('build'),
                'test': BuildSystem.BUILD_SCRIPTS[system].get('test'),
                'lint': BuildSystem.BUILD_SCRIPTS[system].get('lint')
            }

        return None

    @staticmethod
    def run_command(command, cwd=None, timeout=300):
        """Execute a build/test command and return output"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': command
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Command timed out after {timeout} seconds',
                'command': command
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'command': command
            }

    @staticmethod
    def build_project(repo_path):
        """Build the project and return status"""
        build_config = BuildSystem.get_build_command(repo_path)

        if not build_config:
            return {
                'success': False,
                'error': 'Could not detect build system'
            }

        result = BuildSystem.run_command(
            build_config['build'],
            cwd=repo_path
        )

        return {
            'system': build_config['system'],
            'build_result': result,
            'success': result['success']
        }

    @staticmethod
    def test_project(repo_path):
        """Run tests on the project"""
        build_config = BuildSystem.get_build_command(repo_path)

        if not build_config:
            return {
                'success': False,
                'error': 'Could not detect build system'
            }

        result = BuildSystem.run_command(
            build_config['test'],
            cwd=repo_path,
            timeout=600
        )

        return {
            'system': build_config['system'],
            'test_result': result,
            'success': result['success']
        }

    @staticmethod
    def lint_project(repo_path):
        """Run linting on the project"""
        build_config = BuildSystem.get_build_command(repo_path)

        if not build_config:
            return {
                'success': False,
                'error': 'Could not detect build system'
            }

        result = BuildSystem.run_command(
            build_config['lint'],
            cwd=repo_path,
            timeout=300
        )

        return {
            'system': build_config['system'],
            'lint_result': result,
            'success': result['success']
        }
