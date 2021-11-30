# lexfuns.py
from cythonparser import *

class file(statebox):
    def endtok(self, t:endtok): return
    def tabtok(self, t:tabtok):
        self.optional(statements)
        assert self.gettabtok()
        self.next()
        assert self.getendtok()

class statements(statebox):
    def lextok(self):
        return parsernode(statements, None, *self.rep1(statement))

class statement(statebox):
    def tabtok(self, t:tabtok):
        self.next(); self.lextok()
    def optok(self, t: optok):
        if t.op in compound_stmt.ops:
            return compound_stmt(self.p)
        elif t.op in simple_stmt.ops:
            return simple_stmts(self.p)

class simple_stmts(statebox):
    def lextok(self):
        return None

class simple_stmt(statebox):
    ops = {'return', 'import', 'raise', 'pass', 'del',
        'yield', 'assert', 'break','continue',
        'global', 'nonlocal', '*', '-', '+', '~'}

    def optok(self, t:optok):
        raise NotImplementedError()

class atom(statebox):
    def lextok(self) -> 'parsernode|None':
        return None # TODO

class genexp(statebox):
    def lextok(self) -> 'parsernode|None':
        return None # TODO

class args(statebox):
    def lextok(self) -> 'parsernode|None':
        # TODO fill out
        if r := assignment_expression(self.p):
            return r
        elif r := expression(self.p):
            assert self.getoptok(':=') is None
            return r

class arguments(statebox):

    @dataclass
    class empty(parsernode):
        op:optok

    def optok(self, para_op:optok) -> 'parsernode|None':
        self.next()
        if a := args(self.p):
            pass
        else: r = self.empty(para_op)
        assert self.getoptok(')')
        return r

class primary(statebox):
    @dataclass
    class attributeref(parsernode):
        op:optok
        a:parsernode
        name:idftok

    def lextok(self) -> 'parsernode|None':
        if r := atom(self.p):
            while tok := self.getoptok('.', '(', '['):
                self.next()
                if tok.op == '.':
                    assert (name := self.getidftok())
                    r = self.attributeref(tok, r, name)
                elif tok.op == '(':
                    b = genexp()
                    



class power(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := primary(self.p):
            if op := self.getoptok('**'):
                self.next(); b = factor(self.p, parserfail)
                return self.node(op, a, b)
            return a

class factor(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        r:parsernode

    def getops(self):
        while op := self.getoptok('+','-','~'):
            yield op; self.next()

    def lextok(self):
        if ops := list(self.getops()):
            r = power(self.p, parserfail)
            ops.reverse()
            for op in ops: r = self.node(op, r)
            return r
        return power(self.p)

class term(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := factor(self.p):
            while op := self.getoptok('*','/','//','%','@'):
                self.next(); b = factor(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class sum_expr(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := term(self.p):
            while op := self.getoptok('+', '-'):
                self.next(); b = term(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class shift_expr(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := sum_expr(self.p):
            while op := self.getoptok('<<', '>>'):
                self.next(); b = sum_expr(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class bitwise_and(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := shift_expr(self.p):
            while op := self.getoptok('&'):
                self.next(); b = shift_expr(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class bitwise_xor(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := bitwise_and(self.p):
            while op := self.getoptok('^'):
                self.next(); b = bitwise_and(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class bitwise_or(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := bitwise_xor(self.p):
            while op := self.getoptok('|'):
                self.next(); b = bitwise_xor(self.p, parserfail)
                a = self.node(op, a, b)
            return a

class comparison(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    ops = {'==', '!=', '<=', '<', '>=', '>', 'in'}

    def lextok(self):
        if a := bitwise_or(self.p):
            self.next()
            if op := self.bitop():
                self.next(); b = bitwise_or(self.p, parserfail)
                return self.node(op, a, b)
            return a

    def bitop(self):
        if not (tok := self.getoptok()): return None
        if tok.op in self.ops: return tok
        elif tok.op == 'is':
            self.next()
            if self.getoptok('not'):
                return optok(tok.info, 'is not')
            return tok
        elif tok.op == 'not':
            self.next(); assert self.getoptok('in')
            return optok(tok.info, 'not in')
        return None

class inversion(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        r:parsernode
        b:bool

    def lextok(self):
        bool_flip, first_op = True, None
        while op := self.getoptok('not'):
            first_op = first_op or op
            bool_flip = not bool_flip
            self.next()
        if first_op:
            r = comparison(self.p, parserfail)
            return self.node(first_op, bool_flip, r)
        return comparison(self.p)

class conjunction(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := inversion(self.p):
            while op := self.getoptok('and'):
                self.next(); b = inversion(self.p, parserfail)
                return self.node(op, a, b)
            return a

class disjunction(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        a:parsernode
        b:parsernode

    def lextok(self):
        if a := conjunction(self.p):
            while op := self.getoptok('or'):
                self.next(); b = conjunction(self.p, parserfail)
                return self.node(op, a, b)
            return a

class lambdadef(statebox): pass
class expression(statebox):
    @dataclass
    class node(parsernode):
        ifop:optok
        elseop:optok
        a:parsernode
        b:parsernode
        c:parsernode

    def lextok(self):
        if self.getoptok('lambda'):
            self.next(); return lambdadef(self.p, parserfail)
        elif a := disjunction(self.p):
            if ifop := self.getoptok('if'):
                self.next(); b = disjunction(self.p, parserfail)
                assert (elseop := self.getoptok('else')); self.next()
                c = expression(self.p, parserfail)
                return self.node(ifop, elseop, a, b, c)
            return a

class assignment_expression(statebox):
    @dataclass
    class node(parsernode):
        name:idftok
        op:optok
        r:parsernode

    @dataclass
    class name(parsernode):
        name:idftok

    def lextok(self):
        if name := self.getidftok():
            if op := self.getoptok(':='):
                self.next(); exp = expression(self.p, parserfail)
                return self.node(name, op, exp)
            return self.name(name)

class named_expression(statebox):
    def lextok(self):
        if r := assignment_expression(self.p):
            return r
        elif r := expression(self.p):
            assert self.getoptok(':=') is None
            return r

class block(statebox): pass

class function_def(statebox): pass

class if_stmt(statebox):

    @dataclass
    class elifnode(parsernode):
        op:optok
        elif_test:parsernode
        r:parsernode

    @dataclass
    class elsenode(parsernode):
        op:optok
        r:parsernode

    @dataclass
    class ifnode(parsernode):
        op:optok
        if_test:parsernode
        nodes:'tuple[parsernode, ...]'

    def getelifs(self):
        while op := self.getoptok('elif'):
            assert (a := named_expression(self.p))
            assert self.getoptok(':'); self.next()
            yield self.elifnode(op, a, block(self.p, parserfail))

    def getelse(self):
        if op := self.getoptok('else'):
            assert self.getoptok(':'); self.next()
            yield self.elsenode(op, block(self.p, parserfail))

    def optok(self, ifop:optok):
        self.next(); a = named_expression(self.p, parserfail)
        assert self.getoptok(':'); self.next()
        b = block(self.p, parserfail)
        return self.ifnode(ifop, a, b, *self.getelifs, *self.getelse)

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

    def optok(self, t:optok):
        return self.ops[t.op](self.p)
