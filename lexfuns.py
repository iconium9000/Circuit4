# lexfuns.py
from cythonparser import *

class file(statebox):
    def lextok(self) -> 'lextok|None':
        if tok := self.tabtok_next():
            self.p.indent = tok.tabs
            r = statements(self.p)
            self.assert_syntax(self.endtok())
            return r

class statements(statebox):

    @dataclass
    class node(lextok):
        args:'list[lextok]'

    def getstmts(self):
        while r := statement(self.p): yield r

    def lextok(self):
        args = list(self.getstmts())
        if args: return self.node(args)

class statement(statebox):
    def lextok(self) -> 'lextok|None':
        if self.tabtok(): return
        r = compound_stmt(self.p) or simple_stmts(self.p)
        self.assert_syntax(tok := self.tabtok())
        self.assert_syntax(tok.tabs <= self.p.indent)
        if tok.tabs == self.p.indent: self.next()
        return r


@dataclass
class attributeref(lextok):
    prim:lextok
    op:optok
    name:idftok

class yield_expr(statebox):
    pass # TODO

class annotated_rhs(statebox):
    def lextok(self) -> 'lextok|None':
        return yield_expr(self.p) or star_expressions(self.p)

class single_subscript_attribute_target(statebox):
    pass # TODO

class single_target(statebox):
    pass # TODO

class vardef(statebox):

    @dataclass
    class name(lextok):
        name:idftok

    @dataclass
    class subscript(lextok):
        prim:lextok
        slices:lextok

    @dataclass
    class node(lextok):
        target:lextok
        op:optok
        hint:lextok
        assign:'lextok|None'

    def lextok(self) -> 'lextok|None':
        if tok := self.idftok_next():
            target = self.name(tok)
        elif op := self.optok_next('('):
            target = single_target(self.p, syntax=True)
            self.assert_syntax(self.optok_next(')'))
        elif (prim := t_primary(self.p)) and (tok := self.optok('.','[','(')):
            self.assert_syntax(tok.op != '(')
            if tok.op == '.':
                self.next()
                self.assert_syntax(name := self.idftok_next())
                target = attributeref(prim, tok, name)
            elif tok.op == '[':
                r = slices(self.p, syntax=True)
                target = self.subscript(prim, r)
        else: return

        if not (op := self.optok_next(':')): return
        elif not (hint := expression(self.p)): return
        if self.optok_next('='):
            a = annotated_rhs(self.p, syntax=True)
            return self.node(target, op, hint, a)
        return self.node(target, op, hint, None)

class star_targets_tuple_seq(statebox):
    pass # TODO

class star_targets_list_seq(statebox):
    pass # TODO

class star_atom(statebox):
    tracking = False

    @dataclass
    class node(lextok):
        op:optok

    def lextok(self) -> 'lextok|None':
        if tok := self.optok_next('(','['):
            if tok.op == '(':
                a = target_with_star_atom(self.p) or star_targets_tuple_seq(self.p)
                self.assert_syntax(self.optok_next(')'))
                return a or self.node(tok)
            a = star_targets_list_seq(self.p)
            self.assert_syntax(self.optok_next(']'))
            return a or self.node(tok)

class target_with_star_atom(statebox):
    tracking = False

    @dataclass
    class node(lextok):
        prim:lextok
        slices:lextok

    def lextok(self) -> 'lextok|None':
        if prim := t_primary(self.p):
            tok:optok = self.optok('.','[','(')
            self.assert_syntax(tok.op != '(')
            if tok.op == '.':
                self.next()
                self.assert_syntax(name := self.idftok_next())
                return attributeref(prim, tok, name)
            return self.node(prim, slices(self.p, syntax=True))
        return self.idftok_next() or star_atom(self.p)

class star_target(statebox):

    @dataclass
    class node(lextok):
        op:optok
        target:lextok

    def lextok(self) -> 'lextok|None':
        if op := self.optok_next('*'):
            self.assert_syntax(not self.optok('*'))
            t  = target_with_star_atom(self.p, syntax=True)
            return self.node(op, t)
        return target_with_star_atom(self.p)

class star_target_comma(statebox):
    def lextok(self) -> 'lextok|None':
        if (t := star_target(self.p)) and self.optok_next(','):
            return t

class star_targets(statebox):
    @dataclass
    class node(lextok):
        args:'list[lextok]'
    def gettargets(self):
        while t := star_target_comma(self.p): yield t
        if t := star_target(self.p): yield t
    def lextok(self) -> 'lextok|None':
        if args := list(self.gettargets()):
            return self.node(args)

class star_targets_assign(statebox):
    def lextok(self) -> 'lextok|None':
        if t := star_targets(self.p) and self.optok_next('='):
            return t

class assign_target(statebox):

    @dataclass
    class node(lextok):
        args:'list[lextok]'
        expr:lextok

    def gettargets(self):
        while t := star_targets_assign(self.p):
            yield t

    def lextok(self) -> 'lextok|None':
        if args := list(self.gettargets()):
            expr = yield_expr(self.p) or star_expressions(self.p, syntax=True)
            self.assert_syntax(not self.optok('='))
            return self.node(args,expr)

class augassign_target(statebox):
    ops = { '+=','-=','*=','@=','/=','%=','&=','|=','^=','<<=','>>=','**=','//=' }

    @dataclass
    class node(lextok):
        target:lextok
        op:optok
        expr:lextok

    def lextok(self) -> 'lextok|None':
        if (t := single_target(self.p)) or (op := self.optok_next(*self.ops)):
            r = yield_expr(self.p) or star_expressions(self.p, syntax=True)
            return self.node(t,op,r)

class assignment(statebox):
    def lextok(self) -> 'lextok|None':
        return vardef(self.p) or assign_target(self.p) or augassign_target(self.p)

class star_expressions(statebox): pass
class return_stmt(statebox): pass
class import_stmt(statebox): pass
class raise_stmt(statebox): pass
class del_stmt(statebox): pass
class yield_stmt(statebox): pass
class assert_stmt(statebox): pass
class global_stmt(statebox): pass
class nonlocal_stmt(statebox): pass
class pass_stmt(statebox): pass
class break_stmt(statebox): pass
class continue_stmt(statebox): pass

class simple_stmt(statebox):
    ops = {
        'return': return_stmt,
        'import': import_stmt,
        'raise': raise_stmt,
        'pass': pass_stmt,
        'del': del_stmt,
        'yield': yield_stmt,
        'assert': assert_stmt,
        'break': break_stmt,
        'continue': continue_stmt,
        'global': global_stmt,
        'nonlocal': nonlocal_stmt
    }

    def lextok(self) -> 'lextok|None':
        if tok := self.optok(self.ops):
            return self.ops[tok.op](self.p)
        return assignment(self.p) or star_expressions(self.p)

class simple_stmts(statebox):

    @dataclass
    class node(lextok):
        args:'list[lextok]'

    def getstmts(self):
        while r := simple_stmt(self.p):
            yield r
            if not self.optok_next(';'): break
        self.assert_syntax(self.tabtok())

    def lextok(self):
        if args := list(*self.getstmts()):
            return self.node(args)

class list_listcomp(statebox):
    tracking = False
    pass # TODO
class tuple_group_genexp(statebox):
    tracking = False
    pass # TODO
class dict_set_dictcomp_setcomp(statebox):
    tracking = False
    pass # TODO

class strings(statebox):
    @dataclass
    class node(lextok):
        strings:tuple[strtok]
    def getstrings(self):
        while tok := self.strtok_next(): yield tok
    def lextok(self) -> 'lextok|None':
        if strings := (*self.getstrings(),):
            return self.node(strings)

class atom(statebox):
    def lextok(self) -> 'lextok|None':
        if tok := self.idftok_next(): return tok
        elif tok := self.optok():
            if tok.op in ('...', 'True','False','None'):
                self.next(); return tok
            elif tok.op == '[': return list_listcomp(self.p)
            elif tok.op == '(': return tuple_group_genexp(self.p)
            elif tok.op == '{': return dict_set_dictcomp_setcomp(self.p)
        elif tok := self.numtok_next(): return tok
        else: return strings(self.p)

class t_primary(statebox):

    class name(statebox):
        def lextok(self) -> 'lextok|None':
            if self.optok_next() and (name := self.idftok_next()):
                return name

    @dataclass
    class node(lextok):
        a:lextok
        b:lextok

    def lextok(self) -> 'lextok|None':        
        if a := atom(self.p):
            while tok := self.optok('(','[','.'):
                if tok.op == '[': b = slices(self.p)
                elif tok.op == '(':
                    b = genexp(self.p) or arguments(self.p)
                elif name := self.name(self.p):
                    b = attributeref(a, tok, name)
                if b: a = self.node(a, b)
                else: return a

class genexp(statebox):
    tracking = False
    pass # TODO

class starred_expression(statebox):
    @dataclass
    class node(lextok):
        op:optok
        r:lextok

    def lextok(self) -> 'lextok|None':
        if op := self.optok_next('*'):
            r = expression(self.p, syntax=True)
            return self.node(op, r)

class kwarg(statebox):
    @dataclass
    class node(lextok):
        op:optok
        name:idftok
        r:lextok

    def lextok(self) -> 'lextok|None':
        if name := self.idftok_next():
            self.assert_syntax(tok := self.optok_next('='))
            r = expression(self.p, syntax=True)
            return self.node(tok, name, r)

class argument(statebox):
    def lextok(self) -> 'lextok|None':
        if r := starred_expression(self.p):
            return r
        elif r := assignment_expression(self.p) or expression(self.p):
            if self.optok('='): return
            return r

class kwarg_or_starred(statebox):
    def lextok(self) -> 'lextok|None':
        if r := kwarg(self.p): return r
        elif r := starred_expression(self.p): return r

class kwarg_or_double_starred(statebox):
    @dataclass
    class node(lextok):
        op:optok
        r:lextok

    def lextok(self) -> 'lextok|None':
        if r := kwarg(self.p): return r
        elif op := self.optok_next('**'):
            r = expression(self.p, syntax=True)
            return self.node(op, r)

class arguments(statebox):
    tracking = False

    @dataclass
    class node(lextok):
        op:optok
        args:'list[lextok]'

    def getargs(self):
        if self.optok_next(')'): return
        for f in (argument, kwarg_or_starred, kwarg_or_double_starred):
            while arg := f(self.p):
                yield arg
                self.assert_syntax(tok := self.optok_next(',',')'))
                if tok.op == ')': return
        self.assert_syntax(self.optok_next(')'))

    def lextok(self) -> 'lextok|None':
        if op := self.optok_next('('):
            return self.node(op, list(self.getargs()))

class slice(statebox):

    @dataclass
    class node(lextok):
        opA:optok
        opB:'optok|None'
        a:'lextok|None'
        b:'lextok|None'
        c:'lextok|None'

    def lextok(self) -> 'lextok|None':
        a = expression(self.p)
        if opA := self.optok_next(':'):
            b = expression(self.b)
            if opB := self.optok_next(':'):
                c = expression(self.b)
            else: c = None
            return self.node(opA, opB, a, b, c)

class slices(statebox):
    tracking = False

    @dataclass
    class node(lextok):
        op:optok
        args:'list[lextok]'

    def getslices(self):
        while r := slice(self.p) or named_expression(self.p):
            yield r
            self.assert_syntax(tok := self.optok_next(',',']'))
            if tok.op == ']': return
        self.assert_syntax(tok := self.optok_next(']'))

    def lextok(self) -> 'lextok|None':
        if op := self.optok_next('['):
            return self.node(op, list(self.getslices()))

class primary(statebox):

    @dataclass
    class call(lextok):
        op:optok
        a:lextok
        arg:lextok

    def lextok(self) -> 'lextok|None':
        if a := atom(self.p):
            while tok := self.optok('.', '(', '['):
                if tok.op == '.':
                    self.next()
                    self.assert_syntax(name := self.idftok_next())
                    a = attributeref(a, tok, name)
                elif tok.op == '(':
                    b = genexp(self.p) or arguments(self.p, syntax=True)
                    a = self.call(tok, a, b)
                elif tok.op == '[':
                    b = slices(self.p, syntax=True)
                    a = self.call(tok, a, b)
            return a

class power(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := primary(self.p):
            if op := self.optok_next('**'):
                b = factor(self.p, syntax=True)
                return self.node(op, a, b)
            return a

class factor(statebox):
    @dataclass
    class node(lextok):
        op:optok
        r:lextok

    def getops(self):
        while op := self.optok_next('+','-','~'):
            yield op

    def lextok(self):
        if ops := list(self.getops()):
            r = power(self.p, syntax=True)
            ops.reverse()
            for op in ops: r = self.node(op, r)
            return r
        return power(self.p)

class term(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := factor(self.p):
            while op := self.optok_next('*','/','//','%','@'):
                b = factor(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class sum_expr(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := term(self.p):
            while op := self.optok_next('+', '-'):
                b = term(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class shift_expr(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := sum_expr(self.p):
            while op := self.optok_next('<<', '>>'):
                b = sum_expr(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class bitwise_and(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := shift_expr(self.p):
            while op := self.optok_next('&'):
                b = shift_expr(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class bitwise_xor(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := bitwise_and(self.p):
            while op := self.optok_next('^'):
                b = bitwise_and(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class bitwise_or(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := bitwise_xor(self.p):
            while op := self.optok_next('|'):
                b = bitwise_xor(self.p, syntax=True)
                a = self.node(op, a, b)
            return a

class comparison(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    ops = {'==', '!=', '<=', '<', '>=', '>', 'in'}

    def lextok(self):
        if a := bitwise_or(self.p):
            if op := self.bitop_next():
                b = bitwise_or(self.p, syntax=True)
                return self.node(op, a, b)
            return a

    def bitop_next(self):
        if not (tok := self.optok_next()): return
        if tok.op in self.ops: return tok
        elif tok.op == 'is':
            if self.optok_next('not'):
                return optok(tok.info, 'is not')
            return tok
        elif tok.op == 'not':
            self.assert_syntax(self.optok_next('in'))
            return optok(tok.info, 'not in')

class inversion(statebox):
    @dataclass
    class node(lextok):
        op:optok
        r:lextok
        b:bool

    def lextok(self):
        bool_flip, first_op = True, None
        while op := self.optok_next('not'):
            first_op = first_op or op
            bool_flip = not bool_flip
        if first_op:
            r = comparison(self.p, syntax=True)
            return self.node(first_op, bool_flip, r)
        return comparison(self.p)

class conjunction(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := inversion(self.p):
            while op := self.optok_next('and'):
                b = inversion(self.p, syntax=True)
                return self.node(op, a, b)
            return a

class disjunction(statebox):
    @dataclass
    class node(lextok):
        op:optok
        a:lextok
        b:lextok

    def lextok(self):
        if a := conjunction(self.p):
            while op := self.optok_next('or'):
                b = conjunction(self.p, syntax=True)
                return self.node(op, a, b)
            return a

class lambdadef(statebox): pass
class expression(statebox):
    @dataclass
    class node(lextok):
        ifop:optok
        elseop:optok
        a:lextok
        b:lextok
        c:lextok

    def lextok(self):
        if self.optok_next('lambda'):
            return lambdadef(self.p, syntax=True)
        elif a := disjunction(self.p):
            if ifop := self.optok_next('if'):
                b = disjunction(self.p, syntax=True)
                self.assert_syntax(elseop := self.optok_next('else'))
                c = expression(self.p, syntax=True)
                return self.node(ifop, elseop, a, b, c)
            return a

class assignment_expression(statebox):
    @dataclass
    class node(lextok):
        name:idftok
        op:optok
        r:lextok

    @dataclass
    class name(lextok):
        name:idftok

    def lextok(self):
        if name := self.idftok_next():
            if op := self.optok_next(':='):
                exp = expression(self.p, syntax=True)
                return self.node(name, op, exp)
            return self.name(name)

class named_expression(statebox):
    def lextok(self):
        if r := assignment_expression(self.p):
            return r
        elif r := expression(self.p):
            self.assert_syntax(self.optok(':=') is None)
            return r

class block(statebox):
    def lextok(self) -> 'lextok|None':
        if tok := self.tabtok_next():
            self.assert_syntax(tok.tabs > self.p.indent)
            indent = self.p.indent
            self.p.indent = tok.tabs
            r = statements(self.p, syntax=True)
            self.assert_syntax(tok := self.tabtok())
            self.assert_syntax(self.p.indent > tok.tabs)
            self.assert_syntax(indent >= tok.tabs)
            if indent == tok.tabs: self.next()
            return r
        raise NotImplementedError

class function_def(statebox): pass

class if_stmt(statebox):

    @dataclass
    class elifnode(lextok):
        op:optok
        elif_test:lextok
        r:lextok

    @dataclass
    class elsenode(lextok):
        op:optok
        r:lextok

    class ifnode(lextok):
        def __init__(self, op:optok, if_test:lextok, *nodes:lextok):
            self.op = op
            self.if_test = if_test
            self.nodes = nodes

    def getelifs_else(self):
        while op := self.optok_next('elif'):
            a = named_expression(self.p, syntax=True)
            self.assert_syntax(self.optok_next(':'))
            yield self.elifnode(op, a, block(self.p, syntax=True))
        if op := self.optok_next('else'):
            self.assert_syntax(self.optok_next(':'))
            yield self.elsenode(op, block(self.p, syntax=True))

    def lextok(self):
        if tok := self.optok_next('if'):
            a = named_expression(self.p, syntax=True)
            self.assert_syntax(self.optok_next(':'))
            b = block(self.p, syntax=True)
            return self.ifnode(tok, a, b, *self.getelifs_else())

class class_stmt(statebox): pass
class with_stmt(statebox): pass
class for_stmt(statebox): pass
class while_stmt(statebox): pass
class match_stmt(statebox): pass

class compound_stmt(statebox):
    ops:'dict[str,statebox]' = {
        'def': function_def,
        'if': if_stmt,
        'class': class_stmt,
        'with': with_stmt,
        'for': for_stmt,
        'while': while_stmt,
        'match': match_stmt }

    def lextok(self) -> 'lextok|None':
        if t := self.optok(*self.ops):
            return self.ops[t.op](self.p)

