# cytree.py
from cylexer import *

@dataclass
class tree_range(tree_node):
    node:tree_node
    start:lextok
    end:lextok

@dataclass
class statements_n(tree_node):
    args:list[tree_node]

@dataclass
class if_block_n(tree_node):
    blocks:'tuple[tuple[tree_node,tree_node]|tree_node]'

@dataclass
class assignment_n(tree_node):
    target:tree_node
    expr:tree_node

@dataclass
class dual_op(tree_node):
    a:opstok
    b:opstok

@dataclass
class binary_op_n(tree_node):
    op:str
    a:tree_node
    b:tree_node

@dataclass
class unary_op_n(tree_node):
    op:str
    n:tree_node
