# cyassembler.py
from dataclasses import dataclass

class c_node: pass

@dataclass
class c_inst(c_node):
    i:str
    op=str()

@dataclass
class c_next(c_node):
    i:c_inst
    n:'c_node|None'=None

@dataclass
class c_branch(c_node):
    n:c_inst
    br:dict[str, c_node]

class c_group:

    def __init__(self, *groups:'c_group', n:'c_node|None'=None):
        nodes = [n] if n else []
        for g in groups:
            nodes += g.nodes
        self.nodes = tuple(nodes)
