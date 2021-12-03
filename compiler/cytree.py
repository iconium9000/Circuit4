# cytree.py
from cylexer import *

@dataclass
class tree_range(tree_node):
    node:tree_node
    start_tok:lextok
    next_tok:lextok

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node]

@dataclass
class if_expr_n(tree_node):
    '''
    call test
    if test is true, run expr
    return value of test
    '''

    test:tree_node
    expr:tree_node

@dataclass
class or_block_n(tree_node):
    '''
    calls each test in sequence and 
    stops when one resolves to true
    returns value of last test
    '''

    exprs:'tuple[tree_node]'

@dataclass
class and_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to false
    returns value of last test
    '''

    exprs:'tuple[tree_node]'

@dataclass
class assignment_n(tree_node):
    target:tree_node
    expr:tree_node

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
