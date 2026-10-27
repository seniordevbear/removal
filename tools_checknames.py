"""Resolve every name a module loads against what is actually in scope.

py_compile does not do this, and the class of mistake it catches has cost
five incidents: the TwoCaptcha kwarg twice, a missing `logging` import in
completemailinglistscom, a missing `import re` in manage.py (which silently
reduced every failure reason to the bare word "broker_raised"), and
searchpeoplefreecom reading email_str from the wrong scope - 330 rows.

Scope-aware since 2026-10-27. The previous version walked functions flat,
so it reported two whole classes of correct code:

  * a nested function's parameters, read in its own body, were checked
    against the ENCLOSING function - manage.py's _watchdog_start(max_silence)
    and _settle(step), capture_forms' _launch(fresh_profile), and this
    file's own bind(target, into).
  * a closure reading one of its enclosing function's locals - the `page`
    in gostrata's box(), the `broker_name` in broker_helpers' _has_form().

Both are legal Python, and a checker that cries wolf on legal code stops
being read. Each function is now checked against its own bindings plus
every enclosing scope's, which still catches a name that is only bound in
an unrelated function.
"""
import ast, builtins, os, sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
_STAR_CACHE = {}


def _star_names(module):
    """Public top-level names of `module`, for `from module import *`.

    The sites_scan scripts all do `from sites_scan._template import *` to
    pick up run_scan/state_code/name_search_scan and friends, so without
    this every one of them reported those as unresolved.
    """
    if module in _STAR_CACHE:
        return _STAR_CACHE[module]
    path = os.path.join(_ROOT, *module.split('.')) + '.py'
    names = set()
    try:
        tree = ast.parse(open(path, encoding='utf-8').read())
    except OSError:
        _STAR_CACHE[module] = names          # not a local module: give up quietly
        return names
    explicit = None
    for n in tree.body:
        if isinstance(n, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == '__all__' for t in n.targets):
            try:
                explicit = set(ast.literal_eval(n.value))
            except Exception:
                explicit = None
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                _bind(t, names)
        elif isinstance(n, ast.Import):
            names |= {(a.asname or a.name.split('.')[0]) for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            names |= {(a.asname or a.name) for a in n.names if a.name != '*'}
    names = explicit if explicit is not None else {n for n in names if not n.startswith('_')}
    _STAR_CACHE[module] = names
    return names

_DUNDERS = {'__file__', '__name__', '__doc__', '__package__', '__spec__',
            '__loader__', '__builtins__', '__debug__'}
_FUNC = (ast.FunctionDef, ast.AsyncFunctionDef)
_SCOPE = _FUNC + (ast.Lambda,)


def _bind(target, into):
    if isinstance(target, ast.Name):
        into.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for e in target.elts:
            _bind(e, into)
    elif isinstance(target, ast.Starred):
        _bind(target.value, into)


def _argnames(a):
    out = {x.arg for x in a.args} | {x.arg for x in a.kwonlyargs}
    out |= {x.arg for x in getattr(a, 'posonlyargs', [])}
    if a.vararg:
        out.add(a.vararg.arg)
    if a.kwarg:
        out.add(a.kwarg.arg)
    return out


def _own_nodes(scope):
    """Nodes belonging to this scope: its body, not any nested scope's body.

    Comprehensions are their own scope in Python 3 but their iterables are
    evaluated in the enclosing one, so they are walked here and their
    targets bound here - close enough, and it never hides a missing import.
    """
    out = []
    stack = list(ast.iter_child_nodes(scope))
    while stack:
        n = stack.pop()
        out.append(n)
        if not isinstance(n, _SCOPE + (ast.ClassDef,)):
            stack.extend(ast.iter_child_nodes(n))
    return out


def _bindings(scope):
    """Names this scope binds: parameters, assignments, imports, for/with/except."""
    names = set()
    if isinstance(scope, _SCOPE):
        names |= _argnames(scope.args)
    for n in _own_nodes(scope):
        if isinstance(n, ast.Assign):
            for tg in n.targets:
                _bind(tg, names)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            _bind(n.target, names)
        elif isinstance(n, (ast.For, ast.AsyncFor)):
            _bind(n.target, names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
        elif isinstance(n, ast.Import):
            names |= {(a.asname or a.name.split('.')[0]) for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            if any(a.name == '*' for a in n.names):
                names |= _star_names(n.module or '')
            names |= {(a.asname or a.name) for a in n.names if a.name != '*'}
        elif isinstance(n, ast.withitem) and n.optional_vars:
            _bind(n.optional_vars, names)
        elif isinstance(n, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            for g in n.generators:
                _bind(g.target, names)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            names |= set(n.names)
    return names


def unresolved(path):
    tree = ast.parse(open(path, encoding='utf-8').read())
    miss = set()

    def walk(scope, visible):
        visible = visible | _bindings(scope)
        for n in _own_nodes(scope):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in visible:
                miss.add(n.id)
        for n in _own_nodes(scope):
            if isinstance(n, _SCOPE):
                walk(n, visible)
            elif isinstance(n, ast.ClassDef):
                walk(n, visible)   # class body sees the enclosing scope

    walk(tree, set(dir(builtins)) | _DUNDERS)
    return sorted(miss)


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        m = unresolved(p)
        print(f"  {p:38} {'OK' if not m else 'UNRESOLVED: ' + ', '.join(m)}")
        bad += bool(m)
    sys.exit(1 if bad else 0)
