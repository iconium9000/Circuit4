# cytree.py
from dataclasses import dataclass
import cylexer
import cycompiler as comp
from cycompiler import control, instruction, register

class tree_node:
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        ctrl.error(f'itc not implemented for {self.__class__.__name__}')

@dataclass
class tree_range_n(tree_node):
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
    num:str

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.number_i(next, reg, self.num)

@dataclass
class string_n(tree_node):
    strings:tuple[str]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register('str') for _ in self.strings)
        next = comp.strings_i(next, reg, regs)
        for r,s in tuple(zip(regs, self.strings))[::-1]:
            next = comp.string_i(next, r, s)
        return next

@dataclass
class identifier_n(tree_node):
    name:str

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return comp.identifier_i(next, reg, self.name)

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
        for expr in self.exprs[::-1]:
            next = expr.itc(ctrl, next, register('stmt'))
        return next

@dataclass
class yield_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        if ctrl.yield_to is None:
            ctrl.error("'yield' outside function")
        ctrl.yields = True
        next = comp.bool_i(next, reg, None)
        next = comp.yield_i(next, ctrl.yield_to, ctrl.yield_reg)
        return self.expr.itc(ctrl, next, ctrl.yield_reg)

@dataclass
class hint_n(tree_node):
    idf:tree_node
    hint:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        hint = register('hint')
        next = comp.hint_i(next, reg, hint)
        next = self.idf.itc(ctrl, next, reg)
        return self.hint.itc(ctrl, next, hint)

@dataclass
class kwarg_n(tree_node):
    name:str
    expr:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        expr_reg = register('kw-arg-expr')
        next = comp.kwarg_i(next, reg, self.name, expr_reg)
        return self.expr.itc(ctrl, next, expr_reg)

@dataclass
class star_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        iterator_reg = register('iter-star')
        iterable_reg = register('iter-expr')
        next = comp.star_i(next, reg, iterator_reg)
        next = comp.iter_i(next, iterator_reg, iterable_reg)
        return self.expr.itc(ctrl, next, iterable_reg)

@dataclass
class kw_star_n(tree_node):
    expr:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        iterator_arg = register('kw-iter-star')
        iterable_arg = register('kw-iter-expr')
        next = comp.kw_star_i(next, reg, iterator_arg)
        next = comp.kw_iter_i(next, iterator_arg, iterable_arg)
        return self.expr.itc(ctrl, next, iterable_arg)

@dataclass
class arguments_n(tree_node):
    exprs:tuple[tree_node]

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        regs = tuple(register('args-expr') for _ in self.exprs)
        next = comp.args_i(next, reg, regs)
        for reg, expr in tuple(zip(regs, self.exprs))[::-1]:
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class call_n(tree_node):
    func:tree_node
    args:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        func_reg, args_reg = register('call-func'), register('call-args')
        next = comp.call_i(next, reg, func_reg, args_reg)
        next = self.args.itc(ctrl, next, args_reg)
        return self.func.itc(ctrl, next, func_reg)

@dataclass
class call_target_n(tree_node):
    func:tree_node
    args:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        ctrl.error("cannot assign to function call here.")

@dataclass
class attribute_ref_n(tree_node):
    primary:tree_node
    attrib:str

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        prim_reg = register('prim_reg')
        next = comp.attrib_i(next, reg, prim_reg, self.attrib)
        return self.primary.itc(ctrl, next, prim_reg)

@dataclass
class attribute_target_n(tree_node):
    primary:tree_node
    attrib:str

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        prim_reg = register('prim_reg')
        next = comp.attrib_tar_i(next, reg, prim_reg, self.attrib)
        return self.primary(ctrl, next, prim_reg)

@dataclass
class slice_n(tree_node):
    arg1:'tree_node|None'
    arg2:'tree_node|None'
    arg3:'tree_node|None'

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        reg1 = self.arg1 and register()
        reg2 = self.arg2 and register()
        reg3 = self.arg3 and register()
        next = comp.slice_i(next, reg, reg1, reg2, reg3)
        if reg3: next = self.arg3.itc(ctrl, next, reg3)
        if reg2: next = self.arg2.itc(ctrl, next, reg2)
        if reg1: next = self.arg1.itc(ctrl, next, reg1)
        return next

@dataclass
class subscript_n(tree_node):
    primary:tree_node
    arg:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        arg_target = register('arg_target')
        prim_target = register('prim_target')
        next = comp.subscript_i(next, reg, prim_target, arg_target)
        next = self.arg.itc(ctrl, next, arg_target)
        return self.primary.itc(ctrl, next, prim_target)

@dataclass
class subscript_target_n(tree_node):
    primary:tree_node
    arg:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        arg_target = register('arg_target')
        prim_target = register('prim_target')
        next = comp.subscript_target_i(next, reg, prim_target, arg_target)
        next = self.arg.itc(ctrl, next, arg_target)
        return self.primary.itc(ctrl, next, prim_target)

@dataclass
class identifier_target_n(tree_node):
    name:str

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        return comp.identifier_target_i(next, reg, self.name)

@dataclass
class iter_target_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        expr_reg = register('expr_reg')
        next = comp.iter_target_i(next, reg, expr_reg)
        return self.expr.itc(ctrl, next, expr_reg)

@dataclass
class tuple_target_n(tree_node):
    targets:tuple[tree_node]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register() for _ in self.exprs)
        next = comp.tuple_target_i(next, reg, regs)
        for reg, expr in tuple(zip(regs, self.exprs))[::-1]:
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class tuple_n(tree_node):
    exprs:tuple[tree_node]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        regs = tuple(register('tuple-element') for _ in self.exprs)
        next = comp.tuple_i(next, reg, regs)
        for reg, expr in tuple(zip(regs, self.exprs))[::-1]:
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class list_target_n(tree_node):
    exprs:tuple[tree_node]

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        regs = tuple(register() for _ in self.exprs)
        next = comp.list_target_i(next, reg, regs)
        for reg, expr in tuple(zip(regs, self.exprs))[::-1]:
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class list_n(tree_node):
    exprs:tuple[tree_node]

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        regs = tuple(register('list-element') for _ in self.exprs)
        next = comp.list_i(next, reg, regs)
        for reg, expr in tuple(zip(regs, self.exprs))[::-1]:
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class for_n(tree_node):
    target:tree_node
    iterable:tree_node
    block:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        ctrl_break_to = ctrl.break_to
        ctrl_continue_to = ctrl.continue_to

        stmt_reg = register('for-stmt')
        target_reg = register('for-tar')
        iterable_reg = register('for-iterable')
        iterator_reg = register('for-iterator')

        break_to = next
        continue_to = comp.next_i(None, break_to, target_reg, iterator_reg)

        ctrl.break_to = break_to
        ctrl.continue_to = continue_to
        continue_to.next = self.block.itc(ctrl, continue_to, stmt_reg)
        ctrl.continue_to = ctrl_continue_to
        ctrl.break_to = ctrl_break_to

        next = self.target.itc(ctrl, continue_to, target_reg)
        next = comp.iter_i(next, iterator_reg, iterable_reg)
        return self.iterable.itc(ctrl, next, iterable_reg)

@dataclass
class if_n(tree_node):
    test:tree_node
    true_expr:tree_node
    false_expr:tree_node

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        false_reg = register('false-stmt')
        branch_false = self.false_expr.itc(ctrl, next, false_reg)
        true_reg = register('if-true-stmt')
        branch_true = self.true_expr.itc(ctrl, next, true_reg)
        test_reg = register('if-test')
        next = comp.branch_i(branch_true, branch_false, test_reg)
        return self.test.itc(ctrl, next, test_reg)

@dataclass
class pass_n(tree_node):

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        return next

@dataclass
class continue_n(tree_node):

    def itc(self, ctrl: control, next: instruction, reg: register) -> instruction:
        if ctrl.continue_to is None:
            ctrl.error("'continue' not properly in loop")
        return ctrl.continue_to

@dataclass
class async_n(tree_node):
    expr:tree_node
    # TODO itc

@dataclass
class generator_n(tree_node):
    stmt:tree_node

    # TODO itc

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
        for expr in self.exprs[::-1]:
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
        for expr in self.exprs[::-1]:
            next = comp.branch_i(next, return_to, reg)
            next = expr.itc(ctrl, next, reg)
        return next

@dataclass
class assignment_n(tree_node):
    expr:tree_node
    targets:tuple[tree_node, ...]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        for target in self.targets[::-1]:
            target_reg = register('assign-tar')
            next = comp.assign_i(next, target_reg, reg)
            next = target.itc(ctrl, next, target_reg)
        return self.expr.itc(ctrl, next, reg)

@dataclass
class compare_n(tree_node):
    expr:tree_node
    compares:tuple[tuple[str,tree_node], ...]

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return_to = next
        arga, argb = reg, register('comp-argb')
        for op, expr in self.compares[::-1]:
            arga = register('comp-arga')
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
        arga, argb = register('bin-op-arga'), register('bin-op-argb')
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
        expr_reg = register('unary-op-arg')
        next = comp.unary_op_i(next, self.op, reg, expr_reg)
        return self.expr.itc(ctrl, next, expr_reg)

@dataclass
class await_n(tree_node):
    expr:tree_node

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        expr_reg = register('await-expr')
        next = comp.await_i(next, reg, expr_reg)
        return self.expr.itc(ctrl, next, expr_reg)
