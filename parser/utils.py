import ast
import re
import zipfile
import urllib.request
from io import BytesIO

# ── Keyword-based category detection ──────────────────────────────────────────
CATEGORY_KEYWORDS = {
    'auth':     ['login', 'logout', 'signup', 'register', 'token', 'refresh', 'verify', 'password', 'auth', 'oauth'],
    'users':    ['user', 'account', 'profile', 'me', 'member'],
    'items':    ['item', 'product', 'listing', 'catalog', 'entry'],
    'posts':    ['post', 'article', 'blog', 'comment', 'thread'],
    'admin':    ['admin', 'staff', 'manage', 'dashboard', 'panel'],
    'files':    ['upload', 'file', 'image', 'media', 'attachment'],
    'orders':   ['order', 'cart', 'checkout', 'payment', 'invoice', 'billing'],
    'search':   ['search', 'filter', 'query', 'find', 'lookup'],
    'health':   ['health', 'ping', 'status', 'alive', 'ready'],
    'settings': ['setting', 'config', 'preference', 'option'],
}

def classify_endpoint(path: str, name: str) -> str:
    """Return a best-guess category based on path and function name."""
    text = (path + ' ' + name).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category
    return 'general'

# ── Path parameter extraction ─────────────────────────────────────────────────
def extract_path_params(path: str) -> list:
    """Extract named path parameters from Flask/FastAPI-style route paths."""
    # Matches: {param}, <param>, <type:param>
    return re.findall(r'[{<](?:\w+:)?(\w+)[}>]', path)

# ── Workflow detection ────────────────────────────────────────────────────────
WORKFLOW_PATTERNS = [
    {
        'name': '🔐 Authentication Flow',
        'description': 'Standard registration → login → token usage workflow.',
        'methods': ['POST', 'POST'],
        'keywords': [['register', 'signup'], ['login', 'token']],
    },
    {
        'name': '📋 CRUD Resource Flow',
        'description': 'Create → Read → Update → Delete lifecycle for a resource.',
        'methods': ['POST', 'GET', 'PUT', 'DELETE'],
        'keywords': None,
    },
    {
        'name': '📤 File Upload Flow',
        'description': 'Upload a file → retrieve or process it.',
        'methods': ['POST', 'GET'],
        'keywords': [['upload', 'file', 'image'], ['file', 'media', 'attachment']],
    },
]

def detect_workflows(endpoints: list) -> list:
    """Detect common API workflow patterns from a list of endpoint dicts."""
    detected = []
    names_and_paths = [(ep['name'].lower() + ' ' + ep['path'].lower()) for ep in endpoints]
    
    for pattern in WORKFLOW_PATTERNS:
        if pattern['keywords'] is None:
            methods_present = {ep['method'].upper() for group_eps in [endpoints] for ep in group_eps}
            if {'GET', 'POST', 'PUT', 'DELETE'}.issubset(methods_present):
                detected.append({'name': pattern['name'], 'description': pattern['description']})
            continue
        
        matches = True
        for kws in pattern['keywords']:
            if not any(any(kw in text for kw in kws) for text in names_and_paths):
                matches = False
                break
        if matches:
            detected.append({'name': pattern['name'], 'description': pattern['description']})
    
    return detected

# ── AST visitor ───────────────────────────────────────────────────────────────
class APIRouteVisitor(ast.NodeVisitor):
    def __init__(self, filename=''):
        self.endpoints = []
        self.current_file = filename

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute):
                    # FastAPI: @app.get/post/put/delete/patch('/path')
                    if func.attr in ('get', 'post', 'put', 'delete', 'patch'):
                        path = ''
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                        self._add(node, path, [func.attr.upper()], self.current_file)

                    # Flask/FastAPI: @app.route('/path', methods=[...]) or @app.api_route(...)
                    elif func.attr in ('route', 'api_route'):
                        path = ''
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            path = decorator.args[0].value
                        methods = ['GET']
                        for kw in decorator.keywords:
                            if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                                methods = [e.value for e in kw.value.elts if isinstance(e, ast.Constant)]
                        self._add(node, path, methods, self.current_file)
        self.generic_visit(node)

    # also handle async defs
    visit_AsyncFunctionDef = visit_FunctionDef

    def _add(self, node, path, methods, source_file=''):
        params = extract_path_params(path)
        category = classify_endpoint(path, node.name)
        for method in methods:
            self.endpoints.append({
                'path': path,
                'name': node.name,
                'method': method.upper(),
                'description': ast.get_docstring(node) or '',
                'category': category,
                'path_params': params,
                'source_file': source_file,
            })

# ── Public API ────────────────────────────────────────────────────────────────
def parse_project_zip(zip_file) -> tuple:
    """
    Parse a zip file and return (endpoints, workflows, files_info).
    files_info: list of {name, size, has_routes} dicts
    """
    endpoints = []
    files_info = []
    try:
        with zipfile.ZipFile(zip_file, 'r') as archive:
            for item in archive.namelist():
                if item.endswith('.py'):
                    try:
                        raw = archive.read(item)
                        size = len(raw)
                        content = raw.decode('utf-8')
                        tree = ast.parse(content)
                        visitor = APIRouteVisitor(filename=item)
                        visitor.visit(tree)
                        files_info.append({
                            'name': item,
                            'size': size,
                            'has_routes': len(visitor.endpoints) > 0,
                            'route_count': len(visitor.endpoints),
                        })
                        endpoints.extend(visitor.endpoints)
                    except (SyntaxError, UnicodeDecodeError):
                        files_info.append({'name': item, 'size': 0, 'has_routes': False, 'route_count': 0})
                        continue
    except Exception as e:
        raise RuntimeError(f"Error reading zip file: {e}")

    workflows = detect_workflows(endpoints)
    return endpoints, workflows, files_info


def download_github_zip(github_url: str) -> BytesIO:
    """Download a GitHub repository as a zip into memory."""
    github_url = github_url.rstrip('/')
    for branch in ('main', 'master'):
        zip_url = f"{github_url}/archive/refs/heads/{branch}.zip"
        try:
            req = urllib.request.Request(zip_url, headers={'User-Agent': 'AutoDocAI/1.0'})
            response = urllib.request.urlopen(req)
            if response.status == 200:
                return BytesIO(response.read())
        except urllib.error.HTTPError:
            continue
    raise RuntimeError("Could not download GitHub repo (tried 'main' and 'master'). Verify the URL.")
