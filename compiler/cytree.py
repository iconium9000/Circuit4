# cytree.py
from dataclasses import dataclass
import cylexer
import cycompiler as comp
from cycompiler import context, instruction, register

class tree_node:
    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        ctx.tracing.error(f'itc not implemented for {self.__class__.__name__}')

@dataclass
class tree_range_n(tree_node):
    node:tree_node
    start_tok:cylexer.lextok
    next_tok:cylexer.lextok

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        i = ctx.tracing.update(self.start_tok.tidx, self.next_tok.tidx)
        nxt = self.node.asm(ctx, nxt, ret)
        ctx.tracing.update(*i)
        return nxt

@dataclass
class number_n(tree_node):
    num:str

@dataclass
class string_n(tree_node):
    strings:tuple[str, ...]

@dataclass
class idf_n(tree_node):
    name:str

@dataclass
class bool_n(tree_node):
    value:'bool|None'

@dataclass
class ellipsis_n(tree_node):
    pass

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        for expr in self.exprs[::-1]:
            nxt = expr.asm(ctx, nxt, register('stmt'))
        return nxt

@dataclass
class raise_n(tree_node):
    expr:tree_node

@dataclass
class yield_n(tree_node):
    expr:tree_node

@dataclass
class hint_n(tree_node):
    idf:tree_node
    hint:tree_node

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

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        args = tuple(register(f'arg-{i}') for i in range(len(self.exprs)))
        nxt = comp.args_i(nxt, ret, *args)
        for arg in args:
            nxt = comp.pop_stack_i(nxt, arg, ctx.stack_addr)

        for expr in self.exprs[::-1]:
            arg = register('arg')
            nxt = comp.push_stack_i(nxt, ctx.stack_addr, arg)
            nxt = expr.asm(ctx, nxt, arg)

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        func, args = register('func'), register('args')
        nxt = comp.call_i(nxt, ret, func, args, ctx.stack_addr, ctx.raise_to)
        nxt = comp.pop_stack_i(nxt, func, ctx.stack_addr)
        nxt = self.args.asm(ctx, nxt, args)
        nxt = comp.push_stack_i(nxt, ctx.stack_addr, func)
        return self.func.asm(ctx, nxt, func)

@dataclass
class attribute_ref_n(tree_node):
    primary:tree_node
    attrib:str

@dataclass
class attribute_target_n(tree_node):
    primary:tree_node
    attrib:str

@dataclass
class slice_n(tree_node):
    arg1:'tree_node|None'
    arg2:'tree_node|None'
    arg3:'tree_node|None'

@dataclass
class subscript_n(tree_node):
    primary:tree_node
    arg:tree_node

@dataclass
class subscript_target_n(tree_node):
    primary:tree_node
    arg:tree_node

@dataclass
class idf_target_n(tree_node):
    name:str

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        return comp.idf_target_i(nxt, ret, self.name)

@dataclass
class iter_target_n(tree_node):
    expr:tree_node

@dataclass
class tuple_target_n(tree_node):
    targets:tuple[tree_node, ...]

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_target_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class for_n(tree_node):
    target:tree_node
    iterable:tree_node
    block:tree_node

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        false_inst = self.false_block.asm(ctx, nxt, register('false-stmt'))
        true_inst = self.true_block.asm(ctx, nxt, register('true-stmt'))
        test_true = register('test-true')
        branch = comp.branch_i(true_inst, false_inst, test_true)
        return self.test.asm(ctx, branch, test_true)

@dataclass
class pass_n(tree_node):
    pass

@dataclass
class continue_n(tree_node):
    pass

@dataclass
class async_n(tree_node):
    expr:tree_node

@dataclass
class generator_n(tree_node):
    stmt:tree_node

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
    targets:tuple[tree_node, ...]

    def asm(self, ctx: context, nxt: instruction, ret: register) -> instruction:
        for target in self.targets[::-1]:
            target_reg = register('target')
            nxt = comp.assign_i(nxt, target_reg, ret)
            nxt = comp.pop_stack_i(nxt, ret, ctx.stack_addr)
            nxt = target.asm(ctx, nxt, target_reg)
            nxt = comp.push_stack_i(nxt, ctx.stack_addr, ret)
        return self.expr.asm(ctx, nxt, ret)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

@dataclass
class binary_op_n(tree_node):
    '''
    calls expr_a then expr_b and calls op on return values
    '''
    op:str
    expr_a:tree_node
    expr_b:tree_node

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

@dataclass
class await_n(tree_node):
    expr:tree_node
