"""Resolve every global name a module loads against what it imports/defines.
py_compile does not do this; the TwoCaptcha and logging regressions both
got through it."""
import ast, builtins, sys

def unresolved(path):
    t = ast.parse(open(path, encoding='utf-8').read())
    defined = set(dir(builtins))
    def bind(target, into):
        if isinstance(target, ast.Name): into.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for e in target.elts: bind(e, into)
        elif isinstance(target, ast.Starred): bind(target.value, into)
    for n in ast.walk(t):
        if isinstance(n, ast.Import): defined |= {(a.asname or a.name.split('.')[0]) for a in n.names}
        elif isinstance(n, ast.ImportFrom): defined |= {(a.asname or a.name) for a in n.names}
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): defined.add(n.name)
        elif isinstance(n, ast.Assign):
            for tg in n.targets: bind(tg, defined)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)): bind(n.target, defined)
    miss = set()
    def argnames(a):
        out = {x.arg for x in a.args} | {x.arg for x in a.kwonlyargs} | {x.arg for x in getattr(a, 'posonlyargs', [])}
        if a.vararg: out.add(a.vararg.arg)
        if a.kwarg: out.add(a.kwarg.arg)
        return out
    for fn in [x for x in ast.walk(t) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        local = argnames(fn.args)
        # a lambda inside this function binds its own parameters
        for lam in [x for x in ast.walk(fn) if isinstance(x, ast.Lambda)]:
            local |= argnames(lam.args)
        for n in ast.walk(fn):
            if isinstance(n, ast.Assign):
                for tg in n.targets: bind(tg, local)
            elif isinstance(n, (ast.AugAssign, ast.AnnAssign)): bind(n.target, local)
            elif isinstance(n, (ast.For, ast.AsyncFor)): bind(n.target, local)
            elif isinstance(n, ast.ExceptHandler) and n.name: local.add(n.name)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                local |= {(a.asname or a.name.split('.')[0]) for a in n.names}
            elif isinstance(n, ast.withitem) and n.optional_vars: bind(n.optional_vars, local)
            elif isinstance(n, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
                for g in n.generators: bind(g.target, local)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not fn:
                local.add(n.name)
        for n in ast.walk(fn):
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) \
               and n.id not in local and n.id not in defined:
                miss.add(n.id)
    return sorted(miss)

if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        m = unresolved(p)
        print(f"  {p:34} {'OK' if not m else 'UNRESOLVED: ' + ', '.join(m)}")
        bad += bool(m)
    sys.exit(1 if bad else 0)
