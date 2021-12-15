# cytree.py
from dataclasses import dataclass
import cylexer
from cycompiler import context, context_paths, register

class tree_node:
    def asm(self, ctx:context) -> context_paths:
        name = self.__class__.__name__
        msg = f"asm is not implemented for '{name}'"
        raise NotImplementedError(msg)

@dataclass
class tree_range_n(tree_node):
    node:tree_node
    start_tok:cylexer.lextok
    next_tok:cylexer.lextok
    
    def asm(self, ctx: context) -> context_paths:
        ctx = ctx.setrange(self.start_tok.tidx, self.next_tok.tidx)
        return self.node.asm(ctx)

@dataclass
class program_n(tree_node):
    stmt:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths = self.stmt.asm(ctx)
        raise NotImplementedError('todo')

@dataclass
class int_lit_n(tree_node):
    num:str
    
    def asm(self, ctx: context) -> context_paths:
        return ctx.lit_int(self.num)

@dataclass
class string_n(tree_node):
    strings:tuple[str, ...]

@dataclass
class idf_n(tree_node):
    name:str
    
    def asm(self, ctx: context) -> context_paths:
        return ctx.lookup_idf(self.name)

@dataclass
class bool_n(tree_node):
    value:'bool|None'

@dataclass
class ellipsis_n(tree_node):
    pass

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            ctx = ctx.clearval()
        return paths.join_nxt(ctx)

@dataclass
class raise_n(tree_node):
    expr:tree_node

@dataclass
class yield_n(tree_node):
    expr:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        return ctx.yield_expr(ctx.tail_val()).join(paths)

@dataclass
class hint_n(tree_node):
    trgt:tree_node
    hint:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.trgt.asm(ctx).exclude_nxt()
        ref = ctx.tail_val()
        paths, ctx = self.hint.asm(ctx).exclude_nxt(paths)
        return ctx.hint(ref, ctx.tail_val()).join(paths)

@dataclass
class kwarg_n(tree_node):
    name:str
    expr:tree_node

@dataclass
class star_n(tree_node):
    iterable:tree_node

@dataclass
class kw_star_n(tree_node):
    expr:tree_node

@dataclass
class arguments_n(tree_node):
    exprs:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        values:list[register] = []
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            values.append(ctx.tail_val())
        return ctx.group('args', *values).join(paths)

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.func.asm(ctx).exclude_nxt()
        func = ctx.tail_val()
        paths, ctx = self.args.asm(ctx).exclude_nxt(paths)
        return ctx.call(func, ctx.tail_val()).join(paths)

@dataclass
class attribute_ref_n(tree_node):
    prim:tree_node
    attrib:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        return ctx.attrib(ctx.tail_val(), self.attrib).join(paths)

@dataclass
class attribute_trgt_n(tree_node):
    prim:tree_node
    attrib:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        return ctx.attrib_ref(ctx.tail_val(), self.attrib).join(paths)

@dataclass
class slice_n(tree_node):
    arg1:'tree_node|None'
    arg2:'tree_node|None'
    arg3:'tree_node|None'

@dataclass
class subscript_n(tree_node):
    prim:tree_node
    arg:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        prim = ctx.tail_val()
        paths, ctx = self.prim.asm(ctx).exclude_nxt(paths)
        return ctx.subscript(prim, ctx.tail_val()).join(paths)

@dataclass
class subscript_trgt_n(tree_node):
    prim:tree_node
    arg:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        prim = ctx.tail_val()
        paths, ctx = self.prim.asm(ctx).exclude_nxt(paths)
        return ctx.subscript_ref(prim, ctx.tail_val()).join(paths)

@dataclass
class idf_trgt_n(tree_node):
    name:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = ctx.lookup_idf(self.name).exclude_nxt()
        return ctx.lookup_ref(ctx.tail_val()).join(paths)

@dataclass
class star_trgt_n(tree_node):
    expr:tree_node

@dataclass
class tuple_trgt_n(tree_node):
    trgts:tuple[tree_node, ...]

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        values:list[register] = []
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            values.append(ctx.tail_val())
        return ctx.group('tuple', *values).join(paths)

@dataclass
class list_trgt_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        values:list[register] = []
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            values.append(ctx.tail_val())
        return ctx.group('list', *values).join(paths)

@dataclass
class iter_n(tree_node):
    iterable:tree_node
    pass

@dataclass
class for_n(tree_node):
    trgt:tree_node
    iterable:tree_node
    block:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.iterable.asm(ctx).exclude_nxt()
        paths, ctx = ctx.iterator(ctx.tail_val()).exclude_nxt(paths)
        iterator = ctx.tail_val()

        fctx = ctx.newloop()
        fpaths, fctx = fctx.next_element(iterator).exclude_nxt()
        next_element = fctx.tail_val()
        fpaths, fctx = self.trgt.asm(fctx).exclude_nxt(fpaths)
        fpaths, fctx = fctx.assign(next_element, fctx.tail_val()).exclude_nxt(fpaths)
        fpaths = self.block.asm(fctx).join(fpaths)

        return ctx.loop(fpaths).join(paths)

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.test.asm(ctx).exclude_nxt()
        ctx_true, ctx_false = ctx.branch_assert()
        true_paths = self.true_block.asm(ctx_true)
        false_paths = self.false_block.asm(ctx_false)
        return paths.join(true_paths, false_paths)

@dataclass
class pass_n(tree_node):
    
    def asm(self, ctx: context) -> context_paths:
        return context_paths().join_nxt(ctx.clearval())

@dataclass
class continue_n(tree_node):
    pass

@dataclass
class async_n(tree_node):
    expr:tree_node

@dataclass
class generator_n(tree_node):
    stmt:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        generator_paths = self.stmt.asm(ctx.newframe())
        return ctx.generator(generator_paths)

@dataclass
class or_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to true
    returns value of last test
    '''

    exprs:'tuple[tree_node, ...]'

@dataclass
class and_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to false
    returns value of last test
    '''

    exprs:'tuple[tree_node, ...]'

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    trgts:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        expr = ctx.tail_val()
        trgts:list[register] = []
        for trgt in self.trgts:
            paths, ctx = trgt.asm(ctx).exclude_nxt(paths)
            trgts.append(ctx.tail_val())
        for trgt in trgts:
            paths, ctx = ctx.assign(trgt, expr).exclude_nxt(paths)
        return paths.join_nxt(ctx)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        arg = ctx.tail_val()
        for op, expr in self.compares:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            paths, ctx = ctx.binop(op, arg, arg := ctx.tail_val()).exclude_nxt(paths)
            ctx, nxt = ctx.branch_assert()
            paths = paths.join_nxt(nxt)
        return paths.join_nxt(ctx)

@dataclass
class binary_op_n(tree_node):
    '''
    calls expr_a then expr_b and calls op on return values
    '''
    op:str
    expr_a:tree_node
    expr_b:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr_a.asm(ctx).exclude_nxt()
        arg = ctx.tail_val()
        paths, ctx = self.expr_b.asm(ctx).exclude_nxt(paths)
        return ctx.binop(self.op, arg, ctx.tail_val()).join(paths)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        return ctx.unop(self.op, ctx.tail_val()).join(paths)

@dataclass
class await_n(tree_node):
    expr:tree_node
