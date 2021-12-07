# cytree.py
from dataclasses import dataclass
import cylexer
import cycompiler as comp
from cycompiler import reverse, control, instruction, register

class tree_node:
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        ctrl.error(f'itc not implemented for {self.__class__.__name__}')

@dataclass
class tree_range(tree_node):
    node:tree_node
    start_tok:cylexer.lextok
    next_tok:cylexer.lextok

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        lnum, lidx = ctrl.lnum, ctrl.lidx
        ctrl.lnum = self.start_tok.lnum
        ctrl.lidx = self.start_tok.lidx
        next = self.node.itc(ctrl, next, reg)        
        ctrl.lnum, ctrl.lidx = lnum, lidx
        s = self.start_tok
        e = self.next_tok
        lines = '\n'.join(ctrl.manip.getlines(s.lnum, s.lidx, e.lnum, e.lidx))
        next = comp.comment_i(next, lines)
        return next

@dataclass
class number_n(tree_node):
    str:str

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.number_i(next, reg, self.str)

@dataclass
class string_n(tree_node):
    strings:tuple[str]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register() for _ in self.strings)
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
class yield_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        if ctrl.yield_to is None:
            ctrl.error("'yield' outside function")
        ctrl.yields = True
        next = comp.bool_i(next, reg, None)
        next = comp.yield_i(next, ctrl.yield_to, reg := register())
        return self.expr.itc(ctrl, next, reg)

@dataclass
class hint_n(tree_node):
    var:tree_node
    hint:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = comp.hint_i(next, reg, hint := register())
        next = self.hint.itc(ctrl, next, hint)
        return self.var.itc(ctrl, next, reg)

@dataclass
class star_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        next = comp.star_i(next, reg, reg := register())
        return self.expr.itc(ctrl, next, reg)

@dataclass
class targets_n(tree_node):
    targets:tuple[tree_node]

    # TODO itc

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register() for _ in self.exprs)
        next = comp.tuple_i(next, reg, regs)
        for reg, expr in reverse(tuple(zip(regs, self.exprs))):
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node]
    # TODO itc

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
class async_n(tree_node):
    expr:tree_node
    # TODO itc

@dataclass
class for_expr_n(tree_node):
    target:tree_node
    iterator:tree_node
    expr:tree_node

    # TODO itc

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

    exprs:'tuple[tree_node]'

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        for expr in reverse(self.exprs):
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
class call_n(tree_node):
    fun:tree_node
    args:tree_node

    # TODO itc

@dataclass
class attribute_ref_n(tree_node):
    primary:tree_node
    attrib:str

    # TODO itc

@dataclass
class slice_n(tree_node):
    arg1:'tree_node|None'
    arg2:'tree_node|None'
    arg3:'tree_node|None'

    # TODO itc

@dataclass
class subscript_n(tree_node):
    primary:tree_node
    arg:tree_node

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        arga, argb = reg, register()
        for op, expr in reverse(self.compares):
            arga = register()
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
