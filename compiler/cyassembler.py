# cyassembler.py
from cycompiler import *

def assember(sctx:context):
    stack:list[context] = [sctx]
    labels:list[context] = []

    while stack:
        ctx = stack.pop()
        if ctx._id is None:
            labels.append(ctx)
            ctx._setid(len(labels))

            for n,nctx in tuple(ctx._ctxs.items()):
                pctx = None
                while nctx._skip() and ('n' in nctx._ctxs):
                    pctx = nctx
                    nctx = nctx._ctxs['n']
                if pctx:
                    ctx._ctxs[n] = nctx
                nctx._prevs[id(ctx)] = ctx

            for n in ('e','f','t','n','fs'):
                if n in ctx._ctxs:
                    stack.append(ctx._ctxs[n])

    for ctx in labels:
        print(str(ctx))
