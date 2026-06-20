import ast

class BugVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings = []

    def visit_ExceptHandler(self, node):
        if node.type is None:
            self.findings.append({
                'line': getattr(node, 'lineno', '?'),
                'severity': 'warning',
                'message': 'Bare except clause detected. This can catch unexpected exceptions like KeyboardInterrupt.'
            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        for arg in node.args.defaults + getattr(node.args, 'kw_defaults', []):
            if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                self.findings.append({
                    'line': getattr(arg, 'lineno', '?'),
                    'severity': 'warning',
                    'message': 'Mutable default argument detected. This can lead to unexpected state sharing between calls.'
                })
        self.generic_visit(node)

def run_static_analysis(file_path, file_content):
    findings = []
    try:
        if file_path.endswith('.py'):
            tree = ast.parse(file_content)
            visitor = BugVisitor()
            visitor.visit(tree)
            findings.extend(visitor.findings)
    except Exception as e:
        pass # Gracefully handle syntax errors or AST failures
    return findings
