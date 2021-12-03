# cytree.py
from cylexer import *

@dataclass
class tree_range(tree_node):
    node:tree_node
    start:lextok
    end:lextok

@dataclass
class statements_n(tree_node):
    args:tuple[tree_node]

@dataclass
class if_block_n(tree_node):
    test:tree_node
    blocks:tree_node

@dataclass
class or_block_n(tree_node):
    blocks:'tuple[tree_node]'

@dataclass
class and_block_n(tree_node):
    blocks:'tuple[tree_node]'

@dataclass
class assignment_n(tree_node):
    target:tree_node
    expr:tree_node

@dataclass
class not_op_n(tree_node):
    expr:tree_node

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

@dataclass
class binary_op_n(tree_node):
    op:str
    a:tree_node
    b:tree_node

@dataclass
class unary_op_n(tree_node):
    op:str
    a:tree_node
