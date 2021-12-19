# cycompiler.py

class base_context:
    def op_info(self) -> tuple[str, str]:
        raise NotImplementedError()

class context_paths(base_context):
    def op_info(self) -> tuple[str, str]:
        return 'paths', 'no-op'

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

class context(base_context):

    def op_info(self) -> tuple[str, str]:
        return self._op, self._info

    def _setnext(self, n:'context_paths|context'):
        assert self._next is None
        self._next = n
        return n

    def __init__(self, op:str, info:str='no-op'):
        assert isinstance(op, str)
        self._op = op
        self._info = info
        self._next = None

    def set_stack(self, *joins:context_paths):
        ctx = context('stk-set')
        self._setnext(ctx)
        return context_paths.joinall('stk-set', *joins), ctx

    def join_nxt(self, *joins:context_paths):
        return context_paths.joinall('join', *joins, n=self)

    def push_reg(self, *joins:context_paths):
        return self.inst('push-reg', 'reg', *joins)

    def reg_peeks(self, count:int, *joins:context_paths):
        return self.inst('reg-peeks', str(count), *joins)

    def reg_pops(self, count:int, *joins:context_paths):
        return self.inst('reg-pops', str(count), *joins)

    def del_pops(self, count:int, *joins:context_paths):
        return self.inst('del-pops', str(count), *joins)

    def inst(self, i:str, op:str, *joins:context_paths):
        ictx = context(i, op)
        nctx = context('pass', 'no-op')
        ectx = context('exc', f'{i}({op})')
        ictx._setnext(context_paths(n=nctx, e=ectx))
        self._setnext(ictx)
        return context_paths.joinall('join', *joins, e=ectx), nctx

    def catch_frame(self,
        ctx_start: 'context',
        caught_paths: context_paths,
        *joins:context_paths):
            fctx = context_frame(ctx_start._info, ctx_start, caught_paths)
            nctx = context('pass', 'no-op')
            ectx = context('exc', 'frame')
            paths = context_paths(n=nctx, e=ectx)
            fctx._setnext(paths)
            self._setnext(fctx)
            return context_paths.joinall('join', paths, *joins)

    def setrange(self, s:int, e:int):
        nxt = context('range', f'{s},{e}')
        self._setnext(nxt)
        return nxt

    def branch(self, *joins:context_paths):
        yctx = context('branch', 'reg')
        tctx = context('branch', 'True')
        fctx = context('branch', 'False')
        ectx = context('exc', 'branch')
        yctx._setnext(context_paths(t=tctx, f=fctx, e=ectx))
        self._setnext(yctx)
        return context_paths.joinall('join', *joins, e=ectx), tctx, fctx

class context_frame(context):

    def __init__(self,
        info: str,
        ctx_start:context,
        caught_paths:context_paths):
            super().__init__('frame', info)
            self._ctx_start = ctx_start
            self._caught_paths = caught_paths
            self._exit_paths = context('exit', info)

            # TODO update for different infos
            for ctx in caught_paths._ctxs.values():
                ctx._setnext(self._exit_paths)
