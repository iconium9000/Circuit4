# cycompiler.py
from dataclasses import dataclass
import cyassembler as assy
from cyassembler import c_node

class context_paths:

    @classmethod
    def joinall(cls,
        op:str,
        *joins:'context_paths',
        **ctxs:'context'):
        join_ctxs:dict[str, context] = {}
        for j in joins:
            for n,ctx in j._ctxs.items():
                if n not in join_ctxs:
                    join_ctxs[n] = context(op, 'no-op')
                ctx._setnext(join_ctxs[n])
        for n,ctx in ctxs.items():
            if n not in join_ctxs:
                join_ctxs[n] = context(op, 'no-op')
            ctx._setnext(join_ctxs[n])
        paths = cls.__new__(cls)
        paths._ctxs = join_ctxs
        return paths

    def __init__(self, **ctxs:'context'):
        self._ctxs = ctxs

    def set_stack(self, *joins:'context_paths'):
        nctx = context('stk-set')
        if 'n' in self._ctxs:
            ctxs = self._ctxs.copy()
            ctxs.pop('n')._setnext(nctx)
        else:
            ctxs = self._ctxs
        return self.joinall('stk-set', *joins, **ctxs), nctx

    def reset_stack(self):
        return context_paths.joinall('stk-reset', self)

    def join(self, *joins:'context_paths'):
        return self.joinall('join', self, *joins)

    def split_nxt(self, *joins:'context_paths'):
        nctx = context('join')
        if 'n' in self._ctxs:
            ctxs = self._ctxs.copy()
            ctxs.pop('n')._setnext(nctx)
        else:
            ctxs = self._ctxs
        return self.joinall('join', *joins, **ctxs), nctx

class context:
    
    def _setnext(self, n:'context_paths|context'):
        assert self._next is None
        self._next = n
        return n

    def __init__(self, op:str, info:str='no-op'):
        self._op = op
        self._info = info
        self._frame:'context_paths|context|None' = None
        self._caught_paths:'context_paths|None' = None
        self._next:'context_paths|context|None' = None

    def set_stack(self, *joins:context_paths):
        ctx = context('stk-set')
        self._setnext(ctx)
        return context_paths.joinall('stk-set', *joins), ctx

    def join_nxt(self, *joins:context_paths):
        return context_paths.joinall('join', *joins, n=self)

    def push_reg(self, *joins:context_paths):
        nctx = context('push', 'reg')
        ectx = context('exc', 'push-reg')
        self._setnext(context_paths(n=nctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def reg_peeks(self, count:int, *joins:context_paths):
        nctx = context('peek', str(count))
        ectx = context('exc', f'peek-count({count})')
        self._setnext(context_paths(n=nctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def reg_pops(self, count:int, *joins:context_paths):
        nctx = context('reg-pop', str(count))
        ectx = context('exc', f'reg-pop-count({count})')
        self._setnext(context_paths(n=nctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def del_pops(self, count:int, *joins:context_paths):
        nctx = context('del-pop', str(count))
        ectx = context('exc', f'reg-pop-count({count})')
        self._setnext(context_paths(n=nctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def inst(self, i:str, op:str, *joins:context_paths):
        nctx = context(i, op)
        ectx = context('exc', f'{i}-{op}')
        self._setnext(context_paths(n=nctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def catch_frame(self,
        ctx_start: 'context',
        caught_paths: context_paths,
        *joins:context_paths):
            nctx = context_frame(ctx_start._info, ctx_start, caught_paths)
            ectx = context('exc', 'frame')
            paths = context_paths(n=nctx, e=ectx)
            self._setnext(paths)
            return context_paths.joinall(paths, *joins)

    def setrange(self, s:int, e:int):
        nxt = context('range', f'{s},{e}')
        self._setnext(nxt)
        return nxt

    def branch(self, *joins:context_paths):
        tctx = context('branch', 'True')
        fctx = context('branch', 'False')
        ectx = context('exc', 'branch')
        self._setnext(context_paths(t=tctx, f=fctx, e=ectx))
        return context_paths.joinall('join', *joins, e=ectx), tctx, fctx

class context_frame(context):

    def __init__(self,
        info: str,
        ctx_start:context,
        caught_paths:context_paths):
            super().__init__('frame', info)
            self._ctx_start = ctx_start
            self._caught_paths = caught_paths
