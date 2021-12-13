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

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

@dataclass
class attribute_ref_n(tree_node):
    prim:tree_node
    attrib:str

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

@dataclass
class subscript_trgt_n(tree_node):
    prim:tree_node
    arg:tree_node

@dataclass
class idf_trgt_n(tree_node):
    name:str

@dataclass
class iter_trgt_n(tree_node):
    expr:tree_node

@dataclass
class tuple_trgt_n(tree_node):
    trgts:tuple[tree_node, ...]

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_trgt_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node, ...]

@dataclass
class for_n(tree_node):
    trgt:tree_node
    iterable:tree_node
    block:tree_node

@dataclass
class if_n(tree_node):
    test:tree_node
    true_block:tree_node
    false_block:tree_node

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
    trgts:tuple[tree_node, ...]

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
