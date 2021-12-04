# cytree.py
from cylexer import *

@dataclass
class tree_range(tree_node):
    node:tree_node
    start_tok:lextok
    next_tok:lextok

    def trc(self) -> trace:
        return self.node.trc()

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        # TODO HANDLE RANGE
        return self.node.itc(ctrl, next, reg)

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node]

    def trc(self) -> trace:
        return trace('stats', tuple(n.trc() for n in self.exprs))

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        for expr in reverse(self.exprs):
            next = expr.itc(ctrl, next, reg)
        return next

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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        expr_inst = self.expr.itc(ctrl, next, register())
        if_inst = branch_inst(expr_inst, next, if_reg := register())
        return self.test.itc(ctrl, if_inst, if_reg)

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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        for expr in reverse(self.exprs):
            if return_to != next:
                next = branch_inst(return_to, next, reg)
            next = expr.itc(ctrl, next, reg)
        return next

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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        for expr in reverse(self.exprs):
            if next != return_to:
                next = branch_inst(next, return_to, reg)
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    targets:tuple[tree_node, ...]

    def trc(self) -> trace:
        return trace('assign', (self.target.trc(), self.expr.trc()))
    
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        for target in reverse(self.targets):
            next = assign_inst(next, t_reg := register(), reg)
            next = target.itc(ctrl, next, t_reg)
        return self.expr.itc(ctrl, next, reg)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def trc(self) -> trace:
        return trace('comp',
            (self.expr.trc(),
            *(trace(f'op:"{op}"', (n.trc(),)) for op, n in self.compares)))

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        arga, argb = reg, register()
        for op, expr in reverse(self.compares):
            arga = register()
            if return_to != next:
                next = branch_inst(next, return_to, reg)
            next = compare_inst(next, op, reg, arga, argb)
            next = expr.itc(ctrl, next, argb)
            argb = arga
        return self.expr.itc(ctrl, next, arga)

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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        arga, argb = register(), register()
        next = binary_op_inst(next, self.op, reg, arga, argb)
        next = self.expr_b.itc(ctrl, next, argb)
        return self.expr_a.itc(ctrl, next, arga)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

    def trc(self) -> trace:
        return trace(f'op:"{self.op}"', (self.expr.trc(),))

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = unary_op_inst(next, self.op, reg, arg := register())
        return self.expr.itc(ctrl, next, arg)

@dataclass
class await_n(tree_node):
    expr:tree_node

    def trc(self) -> trace:
        return trace('await', (self.expr.trc(),))

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = await_inst(next, reg, arg := register())
        return self.expr.itc(ctrl, next, arg)
