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
        paths = self.stmt.asm(ctx.newframe())
        return ctx.program(paths)

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
            ctx = ctx.clr_tail_val()
        return paths.join_nxt(ctx)

@dataclass
class raise_n(tree_node):
    expr:tree_node

@dataclass
class yield_n(tree_node):
    expr:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        paths, ctx, expr = ctx.tail_val(paths)
        return ctx.yield_expr(expr).join(paths)

@dataclass
class hint_n(tree_node):
    trgt:tree_node
    hint:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.trgt.asm(ctx).exclude_nxt()
        paths, ctx, ref = ctx.tail_val(paths)
        paths, ctx = self.hint.asm(ctx).exclude_nxt(paths)
        paths, ctx, hint = ctx.tail_val(paths)
        return ctx.hint(ref, hint).join(paths)

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
            paths, ctx, arg = ctx.tail_val(paths)
            values.append(arg)
        return ctx.group('args', *values).join(paths)

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.func.asm(ctx).exclude_nxt()
        paths, ctx, func = ctx.tail_val(paths)
        paths, ctx = self.args.asm(ctx).exclude_nxt(paths)
        paths, ctx, args = ctx.tail_val(paths)
        return ctx.call(func, args).join(paths)

@dataclass
class attribute_ref_n(tree_node):
    prim:tree_node
    attrib:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        paths, ctx, prim = ctx.tail_val(paths)
        return ctx.attrib(prim, self.attrib).join(paths)

@dataclass
class attribute_trgt_n(tree_node):
    prim:tree_node
    attrib:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        paths, ctx, prim = ctx.tail_val(paths)
        return ctx.attrib_ref(prim, self.attrib).join(paths)

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
        paths, ctx, prim = ctx.tail_val(paths)
        paths, ctx = self.prim.asm(ctx).exclude_nxt(paths)
        paths, ctx, subscript = ctx.tail_val(paths)
        return ctx.subscript(prim, subscript).join(paths)

@dataclass
class subscript_trgt_n(tree_node):
    prim:tree_node
    arg:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).exclude_nxt()
        paths, ctx, prim = ctx.tail_val(paths)
        paths, ctx = self.prim.asm(ctx).exclude_nxt(paths)
        paths, ctx, subscript = ctx.tail_val(paths)
        return ctx.subscript_ref(prim, subscript).join(paths)

@dataclass
class idf_trgt_n(tree_node):
    name:str
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = ctx.lookup_idf(self.name).exclude_nxt()
        paths, ctx, trgt = ctx.tail_val(paths)
        return ctx.lookup_ref(trgt).join(paths)

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
            paths, ctx, tupval = ctx.tail_val(paths)
            values.append(tupval)
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
            paths, ctx, listval = ctx.tail_val(paths)
            values.append(listval)
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
        paths, ctx, iterable = ctx.tail_val(paths)
        paths, ctx = ctx.iterator(iterable).exclude_nxt(paths)
        paths, ctx, iterator = ctx.tail_val(paths)

        fctx = ctx.newloop()
        fpaths, fctx = fctx.next_element(iterator).exclude_nxt()
        fpaths, fctx, next_element = fctx.tail_val(fpaths)
        fpaths, fctx = self.trgt.asm(fctx).exclude_nxt(fpaths)
        fpaths, fctx, trgt = fctx.tail_val(fpaths)
        fpaths, fctx = fctx.assign(next_element, trgt).exclude_nxt(fpaths)
        fpaths = self.block.asm(fctx).join(fpaths)

        return ctx.loop(fpaths).join(paths)

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.test.asm(ctx).exclude_nxt()
        paths, ctx_true, ctx_false = ctx.branch(paths)
        true_paths = self.true_block.asm(ctx_true)
        false_paths = self.false_block.asm(ctx_false)
        return paths.join(true_paths, false_paths)

@dataclass
class pass_n(tree_node):
    
    def asm(self, ctx: context) -> context_paths:
        return context_paths().join_nxt(ctx.clr_tail_val())

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

    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            paths, if_true, ctx = ctx.branch(paths)
            paths = paths.join_nxt(if_true)
        return paths.join_nxt(ctx)

@dataclass
class and_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to false
    returns value of last test
    '''

    exprs:'tuple[tree_node, ...]'

    def asm(self, ctx: context) -> context_paths:
        paths = context_paths()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            paths, ctx, if_false = ctx.branch(paths)
            paths = paths.join_nxt(if_false)
        return paths.join_nxt(ctx)

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    trgts:tuple[tree_node, ...]
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        paths, ctx, expr = ctx.tail_val(paths)
        for trgt in self.trgts:
            paths, ctx = trgt.asm(ctx).exclude_nxt(paths)
            paths, ctx, trgt = ctx.tail_val(paths)
            paths, ctx = ctx.assign(trgt, expr).exclude_nxt(paths)
        return paths.join_nxt(ctx)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        paths, ctx, arga = ctx.tail_val(paths)
        for op, expr in self.compares:
            paths, ctx = expr.asm(ctx).exclude_nxt(paths)
            paths, ctx, argb = ctx.tail_val(paths)
            paths, ctx = ctx.binop(op, arga, argb).exclude_nxt(paths)
            arga = argb
            paths, ctx, if_false = ctx.branch(paths)
            paths = paths.join_nxt(if_false)
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
        paths, ctx, arga = ctx.tail_val(paths)
        paths, ctx = self.expr_b.asm(ctx).exclude_nxt(paths)
        paths, ctx, argb = ctx.tail_val(paths)
        return ctx.binop(self.op, arga, argb).join(paths)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node
    
    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).exclude_nxt()
        paths, ctx, arg = ctx.tail_val(paths)
        return ctx.unop(self.op, arg).join(paths)

@dataclass
class await_n(tree_node):
    expr:tree_node
