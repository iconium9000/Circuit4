# cytree.py
from dataclasses import dataclass
import cylexer
from cycompiler import context, context_paths

class tree_node:

    def asm(self, ctx: context) -> context_paths:
        name = self.__class__.__name__
        msg = f"asm not implemented for '{name}'"
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
        paths, fctx = ctx.inst('frame', 'prog')
        fpaths = self.stmt.asm(fctx)
        return ctx.path_inst('program', fpaths, paths)

@dataclass
class int_lit_n(tree_node):
    num:str

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = ctx.inst('int-l', self.num)
        return ctx.join_nxt(paths)

@dataclass
class string_n(tree_node):
    strings:tuple[str, ...]

@dataclass
class idf_n(tree_node):
    name:str

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = ctx.inst('idf-val', self.name)
        return ctx.join_nxt(paths)


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
        paths, ctx = ctx.join_nxt().split_nxt()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.inst('del', 'reg')
        return ctx.join_nxt(paths)

@dataclass
class raise_n(tree_node):
    expr:tree_node

@dataclass
class yield_n(tree_node):
    expr:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.inst('yield', 'reg', paths)
        return ctx.join_nxt(paths).reset_stack()

@dataclass
class hint_n(tree_node):
    trgt:tree_node
    hint:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.trgt.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.hint.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(2, paths)
        paths, ctx = ctx.inst('hint', 'var,hint', paths)
        return ctx.join_nxt(paths).reset_stack()

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
        paths, ctx = ctx.set_stack()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(len(self.exprs), paths)
        paths, ctx = ctx.inst('group', 'args', paths)
        return ctx.join_nxt(ctx).reset_stack()


@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.func.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.args.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(2, paths)
        paths, ctx = ctx.inst('call', 'func,args', paths)
        return ctx.join_nxt(paths).reset_stack()

@dataclass
class attribute_ref_n(tree_node):
    prim:tree_node
    attrib:str

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg()
        paths, ctx = ctx.inst('attrib', self.attrib, paths)
        return ctx.join_nxt(paths).reset_stack()


@dataclass
class attribute_trgt_n(tree_node):
    prim:tree_node
    attrib:str

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg()
        paths, ctx = ctx.inst('attrib-ref', self.attrib, paths)
        return ctx.join_nxt(paths).reset_stack()

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
        paths, ctx = self.prim.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.arg.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(2, paths)
        paths, ctx = ctx.inst('subscript', 'get', paths)
        return ctx.join_nxt(paths).reset_stack()


@dataclass
class subscript_trgt_n(tree_node):
    prim:tree_node
    arg:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.prim.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.arg.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(2, paths)
        paths, ctx = ctx.inst('subscript', 'ref', paths)
        return ctx.join_nxt(paths).reset_stack()


@dataclass
class idf_trgt_n(tree_node):
    name:str

    def asm(self, ctx: context) -> context_paths:
        path, ctx = ctx.inst('idf-ref', self.name)
        return ctx.join_nxt(path)

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
        paths, ctx = ctx.set_stack()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(len(self.exprs), paths)
        paths, ctx = ctx.inst('group', 'tuple', paths)
        return ctx.join_nxt(ctx).reset_stack()


@dataclass
class list_trgt_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = ctx.set_stack()
        for expr in self.exprs:
            paths, ctx = expr.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(len(self.exprs), paths)
        paths, ctx = ctx.inst('group', 'list', paths)
        return ctx.join_nxt(ctx).reset_stack()


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
        paths, ctx = self.iterable.asm(ctx).set_stack()
        paths, ctx = ctx.inst('iterator', 'reg', paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.trgt.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, lctx = ctx.inst('frame', 'loop', paths)
        lpaths, lctx = lctx.reg_peeks(2)
        lpaths, lctx = lctx.inst('next', 'iter,trgt', lpaths)
        lpaths, lctx = self.block.asm(lctx).split_nxt(lpaths)
        lpaths, lctx = lctx.inst('del', 'reg', lpaths)
        lpaths = lctx.join_nxt(lpaths)
        return ctx.path_inst('loop', lpaths, paths).reset_stack()

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.test.asm(ctx).split_nxt()
        paths, tctx, fctx = ctx.branch(paths)
        tpaths, tctx = tctx.inst('del', 'reg')
        fpaths, fctx = fctx.inst('del', 'reg')
        tpaths = self.true_block.asm(tctx).join(tpaths)
        fpaths = self.false_block.asm(fctx).join(fpaths)
        return paths.join(tpaths, fpaths)


@dataclass
class pass_n(tree_node):
    
    def asm(self, ctx: context) -> context_paths:
        return ctx.join_nxt()


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
        paths, gctx = ctx.inst('frame', 'gen')
        gpaths = self.stmt.asm(gctx)
        return ctx.path_inst('generator', gpaths, paths)


@dataclass
class or_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to true
    returns value of last test
    '''

    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context) -> context_paths:
        paths, fctx = ctx.inst('bool', 'False')
        for expr in self.exprs:
            paths, fctx = fctx.inst('del', 'reg', paths)
            paths, fctx = expr.asm(fctx).split_nxt(paths)
            paths, tctx, fctx = fctx.branch(paths)
            paths = tctx.join_nxt(paths)
        return fctx.join_nxt(paths)

@dataclass
class and_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to false
    returns value of last test
    '''

    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context) -> context_paths:
        paths, tctx = ctx.inst('bool', 'True')
        for expr in self.exprs:
            paths, tctx = tctx.inst('del', 'reg', paths)
            paths, tctx = expr.asm(tctx).split_nxt(paths)
            paths, tctx, fctx = tctx.branch(paths)
            paths = fctx.join_nxt(paths)
        return tctx.join_nxt(paths)

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    trgts:tuple[tree_node, ...]

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).set_stack()
        for trgt in self.trgts:
            paths, ctx = ctx.push_reg(paths)
            paths, ctx = trgt.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.push_reg(paths)
            paths, ctx = ctx.reg_peeks(2, paths)
            paths, ctx = ctx.inst('assign', 'val,ref', paths)
            paths, ctx = ctx.del_pops(2, paths)
        return ctx.join_nxt(paths).reset_stack()


@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg()
        if self.compares:
            paths, ctx = ctx.inst('bool', 'True', paths)
        for op,expr in self.compares:
            paths, ctx = ctx.inst('del', 'reg', paths)
            paths, ctx = expr.asm(ctx).split_nxt(paths)
            paths, ctx = ctx.push_reg(paths)
            paths, ctx = ctx.reg_peeks(2, paths)
            paths, ctx = ctx.inst('comp', op, paths)
            paths, tctx, fctx = ctx.branch(paths)
            paths = fctx.join_nxt(paths)
            paths, ctx = tctx.del_pops(-1, paths)
        return ctx.join_nxt(paths).reset_stack()

@dataclass
class binary_op_n(tree_node):
    '''
    calls expr_a then expr_b and calls op on return values
    '''
    op:str
    expr_a:tree_node
    expr_b:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr_a.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = self.expr_b.asm(ctx).split_nxt(paths)
        paths, ctx = ctx.push_reg(paths)
        paths, ctx = ctx.reg_peeks(2, paths)
        paths, ctx = ctx.inst('binop', self.op, paths)
        return ctx.join_nxt(paths).reset_stack()


@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

    def asm(self, ctx: context) -> context_paths:
        paths, ctx = self.expr.asm(ctx).set_stack()
        paths, ctx = ctx.push_reg()
        paths, ctx = ctx.inst('unop', self.op, paths)
        return ctx.join_nxt(paths).reset_stack()

@dataclass
class await_n(tree_node):
    expr:tree_node
