# cytree.py
from cylexer import *

@dataclass
class tree_range:
    node:tree_node
    start:lextok
    end:lextok

@dataclass
class statements_n:
    args:list[tree_node]

def block_n(*args:'tree_node'):
    ret = []
    for arg in args:
        if isinstance(arg, statements_n):
            ret += arg.args
    if not ret: return
    if len(ret) == 1: return ret[0]
    return statements_n(ret)
