# cycompiler.py

class base_context:

    def __init__(self, ctxs:dict[str, 'context']):
        self._ctxs = ctxs

class context_paths(base_context):

    def split_nxt(self, *joins:'context_paths'):
        ctxs, ctx = splitctxs('n', self._ctxs)
        return joinall('pass', *joins, **ctxs), ctx

    def join(self, *joins:'context_paths'):
        return joinall('pass', self, *joins)

    def set_stack(self, *joins:'context_paths'):
        ctxs, ctx = splitctxs('n', self._ctxs)
        return joinall('stk-set', *joins, **ctxs), ctx

    def reset_stack(self):
        return joinall('stk-reset', self)

class context(base_context):

    def _skip(self):
        return self._op in ('pass', 'range-set')

    def _setctxs(self, **ctxs:'context'):
        if not ctxs: return
        if self._skip():
            assert {'n'} == ctxs.keys()
        for n,nctx in ctxs.items():
            assert n not in self._ctxs
            self._ctxs[n] = nctx

    def _setid(self, i:int):
        assert self._id is None
        self._id = f'@{i}'

    def __str__(self):
        f = f'{self._id} {self._op}({self._arg})'
        f += ','.join(f' {n}={ctx._id}' for n,ctx in self._ctxs.items())
        f += f" ({', '.join(ctx._id for ctx in self._prevs.values())})"
        return f

    def __init__(self, op:str, arg:str, **ctxs:'context'):
        super().__init__({})
        self._id = None
        self._op = op
        self._arg = arg
        self._prevs:dict[int,context] = {}
        self._setctxs(**ctxs)

    def set_stack(self, *joins:context_paths):
        nctx = context('stk-set', 'pass')
        self._setctxs(n=nctx)
        return joinall('stk-set', *joins), nctx

    def join_nxt(self, *joins:context_paths):
        return joinall('pass', *joins, n=self)

    def push_reg(self, *joins:context_paths):
        ectx = context('exc', 'push-reg')
        nctx = context('push-reg', 'reg', e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), nctx

    def reg_peeks(self, count:int, *joins:context_paths):
        ectx = context('exc', f'reg-peeks({count})')
        nctx = context('reg-peeks', str(count), e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), nctx

    def reg_pops(self, count:int, *joins:context_paths):
        ectx = context('exc', f'reg-pops({count})')
        nctx = context('reg-pops', str(count), e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), nctx

    def del_pops(self, count:int, *joins:context_paths):
        ectx = context('exc', f'del-pops({count})')
        nctx = context('del-pops', str(count), e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), nctx

    def inst(self, op:str, arg:str, *joins:context_paths):
        ectx = context('exc', f'{op}({arg})')
        nctx = context(op, arg, e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), nctx

    def catch_frame(self, fctx:'context', fpaths:context_paths, *joins:context_paths):
        ectx = context('exc', f'frame-set(s)')
        fs:dict[str, context] = {}
        nctx = context('frame-set', 's', s=fctx, e=ectx)
        for ctx in fpaths._ctxs.values():
            ctx._setctxs(n=nctx)
        joinall('frame-exit', **fs)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, n=nctx, e=ectx)

    def setrange(self, s:int, e:int):
        nctx = context('range-set', f'{s},{e}')
        self._setctxs(n=nctx)
        return nctx

    def branch(self, *joins:context_paths):
        ectx = context('exc', f'frame-set(s)')
        tctx = context('assert', 'True')
        fctx = context('assert', 'False')
        nctx = context('branch', 'reg', t=tctx, f=fctx, e=ectx)
        self._setctxs(n=nctx)
        return joinall('pass', *joins, e=ectx), tctx, fctx

def splitctxs(n:str, ctxs:dict[str, context]):
    sctxs = ctxs.copy()
    if not (ctx := sctxs.pop(n, None)):
        ctx = context('pass', 'pass')
    return sctxs, ctx

def joinctxs(op:str, jctxs:dict[str, context], pctxs:dict[str, context]):
    for n,pctx in pctxs.items():
        if n not in jctxs:
            jctxs[n] = context(op, 'pass')
        pctx._setctxs(n=jctxs[n])

def joinall(op:str, *paths:context_paths, **ctxs:context):
    join_ctxs:dict[str, context] = {}
    for path in paths: joinctxs(op, join_ctxs, path._ctxs)
    joinctxs(op, join_ctxs, ctxs)
    return context_paths(join_ctxs)
