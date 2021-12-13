# cytree.py
from dataclasses import dataclass
import cylexer
import cycompiler as comp
from cycompiler import context, instruction, register

class tree_node:
    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        ctx.tracing.error(f'asm not implemented for {self.__class__.__name__}')

@dataclass
class tree_range_n(tree_node):
    node:tree_node
    start_tok:cylexer.lextok
    next_tok:cylexer.lextok

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        i = ctx.tracing.update(self.start_tok.tidx, self.next_tok.tidx)
        nxt = self.node.asm(ctx, nxt, trgt)
        ctx.tracing.assign_context(nxt)
        ctx.tracing.update(*i)
        return nxt


@dataclass
class program_n(tree_node):
    stmt:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        nxt = self.stmt.asm(ctx, nxt, trgt)
        return comp.prog_i(ctx, nxt)

@dataclass
class int_lit_n(tree_node):
    num:str

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        return comp.int_lit_i(ctx, nxt, trgt, self.num)

@dataclass
class string_n(tree_node):
    strings:tuple[str, ...]

@dataclass
class idf_n(tree_node):
    name:str

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        return comp.idf_i(ctx, nxt, trgt, self.name)

@dataclass
class bool_n(tree_node):
    value:'bool|None'

@dataclass
class ellipsis_n(tree_node):
    pass

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        for expr in self.exprs[::-1]:
            nxt = expr.asm(ctx, nxt, register('stmt'))
        return nxt

@dataclass
class raise_n(tree_node):
    expr:tree_node

@dataclass
class yield_n(tree_node):
    expr:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        addr = ctx.yield_addr
        if addr is not None:
            nxt = comp.copy_i(ctx, nxt, trgt, addr.val)
            jump_reg = comp.jump_reg_i(addr)
            nxt = comp.store_inst_i(ctx, jump_reg, addr.return_addr, nxt)
            return self.expr.asm(ctx, nxt, addr.val)
        ctx.tracing.error("'yield' outside function")

@dataclass
class hint_n(tree_node):
    trgt:tree_node
    hint:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        hint_info = ctx.reg('hint-info')
        nxt = comp.hint_i(ctx, nxt, trgt, hint_info)
        nxt = self.hint.asm(ctx, nxt, hint_info)
        return self.trgt.asm(ctx, nxt, trgt)

@dataclass
class kwarg_n(tree_node):
    name:str
    expr:tree_node

@dataclass
class star_n(tree_node):
    expr:tree_node

@dataclass
class kw_star_n(tree_node):
    expr:tree_node

@dataclass
class arguments_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        args = tuple(ctx.reg(f'arg-{i}') for i in range(len(self.exprs)))
        nxt = comp.args_i(ctx, nxt, trgt, args)
        for arg,expr in tuple(zip(args,self.exprs))[::-1]:
            nxt = expr.asm(ctx, nxt, arg)
        return nxt

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        func = ctx.reg('call-func')
        args = ctx.reg('call-args')
        nxt = comp.call_i(ctx, nxt, trgt, func, args)
        nxt = self.args.asm(ctx, nxt, args)
        return self.func.asm(ctx, nxt, func)

@dataclass
class attribute_ref_n(tree_node):
    prim:tree_node
    attrib:str

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        prim = ctx.reg('prim')
        nxt = comp.attribute_ref_i(ctx, nxt, trgt, prim, self.attrib)
        return self.prim.asm(ctx, nxt, prim)

@dataclass
class attribute_trgt_n(tree_node):
    prim:tree_node
    attrib:str

@dataclass
class slice_n(tree_node):
    arg1:'tree_node|None'
    arg2:'tree_node|None'
    arg3:'tree_node|None'

@dataclass
class subscript_n(tree_node):
    prim:tree_node
    arg:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        prim = ctx.reg('sub-prim')
        arg = ctx.reg('sub-arg')
        nxt = comp.subscript_i(ctx, nxt, trgt, prim, arg)
        nxt = self.arg.asm(ctx, nxt, arg)
        return self.prim.asm(ctx, nxt, prim)

@dataclass
class subscript_trgt_n(tree_node):
    prim:tree_node
    arg:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        prim = ctx.reg('sub-t-prim')
        arg = ctx.reg('sub-t-arg')
        nxt = comp.subscript_target_i(ctx, nxt, trgt, prim, arg)
        nxt = self.arg.asm(ctx, nxt, arg)
        return self.prim.asm(ctx, nxt, prim)

@dataclass
class idf_trgt_n(tree_node):
    name:str

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        return comp.idf_target_i(ctx, nxt, trgt, self.name)

@dataclass
class iter_trgt_n(tree_node):
    expr:tree_node

@dataclass
class tuple_trgt_n(tree_node):
    trgts:tuple[tree_node, ...]

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        args = tuple(ctx.reg(f'tup-{i}') for i in range(len(self.exprs)))
        nxt = comp.tuple_i(ctx, nxt, trgt, args)
        for arg,expr in tuple(zip(args,self.exprs))[::-1]:
            nxt = expr.asm(ctx, nxt, arg)
        return nxt


@dataclass
class list_trgt_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        args = tuple(ctx.reg(f'lst-{i}') for i in range(len(self.exprs)))
        nxt = comp.list_i(ctx, nxt, trgt, args)
        for arg,expr in tuple(zip(args,self.exprs))[::-1]:
            nxt = expr.asm(ctx, nxt, arg)
        return nxt

@dataclass
class for_n(tree_node):
    trgt:tree_node
    iterable:tree_node
    block:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        ctx_continue_addr = ctx.continue_addr
        break_addr = ctx.reg('brk-addr')
        continue_addr = comp.i_loop('cont-addr', ctx, break_addr)
        ctx.continue_addr = continue_addr

        target = ctx.reg('target')
        iterator = ctx.reg('iterator')
        ret_addr = comp.i_return('ret-addr', ctx, register('ret-val'))

        break_to = nxt
        nxt = comp.jump_reg_i(continue_addr)
        nxt = self.block.asm(ctx, nxt, register('for-block'))
        nxt = comp.next_i(ctx, nxt, target, iterator, ret_addr)
        continue_to = nxt

        iterable = ctx.reg('iterable')
        nxt = comp.iter_i(ctx, nxt, iterator, iterable)
        nxt = self.iterable.asm(ctx, nxt, iterable)
        nxt = self.trgt.asm(ctx, nxt, target)

        nxt = comp.store_inst_i(ctx, nxt, ret_addr, break_to)
        nxt = comp.store_inst_i(ctx, nxt, break_addr, break_to)
        nxt = comp.store_inst_i(ctx, nxt, continue_addr, continue_to)

        ctx.continue_addr = ctx_continue_addr
        return nxt

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        false_block = register('if-false-block')
        false_block = self.false_block.asm(ctx, nxt, false_block)
        true_block = register('if-true-block')
        true_block = self.true_block.asm(ctx, nxt, true_block)
        test = register('if-test')
        branch = comp.branch_i(ctx, true_block, false_block, test)
        return self.test.asm(ctx, branch, test)

@dataclass
class pass_n(tree_node):
    
    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        return nxt

@dataclass
class continue_n(tree_node):
    pass

@dataclass
class async_n(tree_node):
    expr:tree_node

@dataclass
class generator_n(tree_node):
    stmt:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        gctx = context(ctx.tracing).return_to().yield_to()
        gnxt = comp.jump_reg_i(gctx.return_addr)
        gnxt = comp.bool_lit_i(gctx, gnxt, gctx.return_addr.val, None)
        gnxt = self.stmt.asm(gctx, gnxt, gctx.reg('gen-block'))
        return comp.generator_i(ctx, nxt, trgt, gnxt, gctx)

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

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        for assign_target in self.trgts[::-1]:
            assign_target_reg = ctx.reg('assign-trgt')
            nxt = comp.assign_i(ctx, nxt, assign_target_reg, trgt)
            nxt = assign_target.asm(ctx, nxt, assign_target_reg)
        return self.expr.asm(ctx, nxt, trgt)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        return_to = nxt
        arga, argb = trgt, register(f'comp-{len(self.compares)}')
        for i, (op, expr) in tuple(enumerate(self.compares))[::-1]:
            arga = register(f'comp-{i}')
            nxt = comp.branch_i(ctx, nxt, return_to, trgt)
            nxt = comp.binary_op_i(ctx, nxt, op, trgt, arga, argb)
            nxt = expr.asm(ctx, nxt, argb)
            argb = arga
        return self.expr.asm(ctx, nxt, arga)

@dataclass
class binary_op_n(tree_node):
    '''
    calls expr_a then expr_b and calls op on return values
    '''
    op:str
    expr_a:tree_node
    expr_b:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        arga = ctx.reg('bin-a')
        argb = ctx.reg('bin-b')
        nxt = comp.binary_op_i(ctx, nxt, self.op, trgt, arga, argb)
        nxt = self.expr_b.asm(ctx, nxt, argb)
        return self.expr_a.asm(ctx, nxt, arga)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

    def asm(self, ctx: context, nxt: instruction, trgt: register) -> instruction:
        arg = ctx.reg('un-arg')
        nxt = comp.unary_op_i(ctx, nxt, self.op, trgt, arg)
        return self.expr.asm(ctx, nxt, arg)

@dataclass
class await_n(tree_node):
    expr:tree_node
