# cytree.py
from cylexer import *

@dataclass
class tree_range(tree_node):
    node:tree_node
    start_tok:lextok
    next_tok:lextok

    def trc(self) -> trace:
        return self.node.trc()

    def itc(self, i: insts, reg: int):
        return self.node.itc(i, reg)

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node]

    def trc(self) -> trace:
        return trace('stats', tuple(n.trc() for n in self.exprs))

    def itc(self, i: insts, reg: int):
        for expr in self.exprs: expr.itc(i, i._reg)

@dataclass
class if_expr_n(tree_node):
    '''
    call test
    if test is true, run expr
    return value of test
    '''

    test:tree_node
    expr:tree_node

    def trc(self) -> trace:
        return trace('if', (self.test.trc(), self.expr.trc()))

    def itc(self, i: insts, reg: int):
        self.test.itc(i, reg)
        idx = i.inst()
        self.expr.itc(i, i._reg)
        i.newinst(idx, 'biff', i._inst, reg)
        return reg

@dataclass
class or_block_n(tree_node):
    '''
    calls each test in sequence and 
    stops when one resolves to true
    returns value of last test
    '''

    exprs:'tuple[tree_node]'

    def trc(self) -> trace:
        return trace('or', tuple(n.trc() for n in self.exprs))

    def itc(self, i: insts, reg: int):
        if not self.exprs: return 0

        branches = tuple(expr.itc(i, reg) or i.inst() for expr in self.exprs)
        for idx in branches:
            i.newinst(idx, 'bift', i._inst, reg)
        return 0

@dataclass
class and_block_n(tree_node):
    '''
    calls each test in sequence and
    stops when one resolves to false
    returns value of last test
    '''

    exprs:'tuple[tree_node]'

    def trc(self) -> trace:
        return trace('and', tuple(n.trc() for n in self.exprs))

    def itc(self, i: insts, reg: int):
        if not self.exprs: return 0

        branches = tuple(expr.itc(i, reg) or i.inst() for expr in self.exprs)
        for idx in branches:
            i.newinst(idx, 'biff', i._inst, reg)

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    targets:tuple[tree_node, ...]

    def trc(self) -> trace:
        return trace('assign', (self.target.trc(), self.expr.trc()))
    
    def itc(self, i: insts, reg: int):
        self.expr.itc(i, reg)
        for target in self.targets:
            target.itc(i, target_reg := i.reg())
            i.newinst(i.inst(), 'assign', target_reg, reg)
        return reg

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def trc(self) -> trace:
        return trace('comp',
            (self.expr.trc(),
            *(trace(f'op:"{op}"', (n.trc(),)) for op, n in self.compares)))

    def itc(self, i: insts, reg: int):
        if not self.compares: return self.expr.itc(i, reg)

        self.expr.itc(i, rega := i.reg())

        insts:list[int] = []
        for op, node in self.compares:
            node.itc(i, regb := i.reg())
            i.newinst(i.inst(), op, reg, rega, regb)
            insts.append(i.inst())
            rega = regb

        for idx in insts:
            i.newinst(idx, 'biff', i._inst, reg)

@dataclass
class binary_op_n(tree_node):
    '''
    calls expr_a then expr_b and calls op on return values
    '''
    op:str
    expr_a:tree_node
    expr_b:tree_node

    def trc(self) -> trace:
        return trace(f'op:"{self.op}"', (self.expr_a.trc(), self.expr_b.trc()))

    def itc(self, i: insts, reg: int):
        self.expr_a.itc(i, rega := i.reg())
        self.expr_b.itc(i, regb := i.reg())
        i.newinst(i.inst(), self.op, reg, rega, regb)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

    def trc(self) -> trace:
        return trace(f'op:"{self.op}"', (self.expr.trc(),))

    def itc(self, i: insts, reg: int):
        self.expr.itc(i, rega := i.reg())
        i.newinst(i.inst(), self.op, reg, rega)

@dataclass
class await_n(tree_node):
    expr:tree_node

    def trc(self) -> trace:
        return trace('await', (self.expr.trc(),))

    def itc(self, i: insts, reg: int):
        self.expr.itc(i, reg)
        i.newinst(i.inst(), 'await', reg)
