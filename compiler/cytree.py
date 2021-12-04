# cytree.py
from dataclasses import dataclass
import cylexer
import cycompiler as comp
from cycompiler import reverse, control, instruction, register

class tree_node:
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        raise NotImplementedError(f'itc not implemented for {self.__class__.__name__}')

@dataclass
class tree_range(tree_node):
    node:tree_node
    start_tok:cylexer.lextok
    next_tok:cylexer.lextok

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        # TODO HANDLE RANGE
        return self.node.itc(ctrl, next, reg)

@dataclass
class number_n(tree_node):
    str:str

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.number_i(next, reg, self.str)

@dataclass
class string_n(tree_node):
    strings:tuple[str]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register() for _ in range(len(self.strings)))
        next = comp.strings_i(next, reg, regs)
        for r,s in reverse(tuple(zip(regs, self.strings))):
            next = comp.string_i(next, r, s)
        return next

@dataclass
class identifier_n(tree_node):
    str:str

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.identifier_i(next, reg, self.str)

@dataclass
class bool_n(tree_node):
    val:'bool|None'

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.bool_i(next, reg, self.val)

@dataclass
class ellipsis_n(tree_node):
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.ellipsis_i(next, reg)

@dataclass
class statements_n(tree_node):
    exprs:tuple[tree_node]

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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        comp.expr_inst = self.expr.itc(ctrl, next, register())
        comp.if_inst = comp.branch_i(comp.expr_inst, next, if_reg := register())
        return self.test.itc(ctrl, comp.if_inst, if_reg)

@dataclass
class or_block_n(tree_node):
    '''
    calls each test in sequence and 
    stops when one resolves to true
    returns value of last test
    '''

    exprs:'tuple[tree_node]'

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        for expr in reverse(self.exprs):
            if return_to != next:
                next = comp.branch_i(return_to, next, reg)
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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        for expr in reverse(self.exprs):
            if next != return_to:
                next = comp.branch_i(next, return_to, reg)
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    targets:tuple[tree_node, ...]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        for target in reverse(self.targets):
            next = comp.assign_i(next, t_reg := register(), reg)
            next = target.itc(ctrl, next, t_reg)
        return self.expr.itc(ctrl, next, reg)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        arga, argb = reg, register()
        for op, expr in reverse(self.compares):
            arga = register()
            if return_to != next:
                next = comp.branch_i(next, return_to, reg)
            next = comp.compare_i(next, op, reg, arga, argb)
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

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        arga, argb = register(), register()
        next = comp.binary_op_i(next, self.op, reg, arga, argb)
        next = self.expr_b.itc(ctrl, next, argb)
        return self.expr_a.itc(ctrl, next, arga)

@dataclass
class unary_op_n(tree_node):
    '''
    calls expr, then calls op on return value
    '''
    op:str
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = comp.unary_op_i(next, self.op, reg, arg := register())
        return self.expr.itc(ctrl, next, arg)

@dataclass
class await_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = comp.await_i(next, reg, arg := register())
        return self.expr.itc(ctrl, next, arg)
