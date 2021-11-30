# lexfuns.py
from os import stat
from cythonparser import *
from out import expression
from parsepnf import parsererror

class file(statebox):
    def lextok(self) -> 'parsernode|None':
        if tok := self.gettabtok():
            self.p.indent = tok.tabs
            r = statements(self.p)
            assert self.getendtok()
            return r

class statements(statebox):

    @dataclass
    class node(parsernode):
        args:'list[parsernode]'

    def getstmts(self):
        while r := statement(self.p):
            yield r
            if self.gettabtok(): return

    def lextok(self):
        args = list(self.getstmts())
        if args: return self.node(args)

class statement(statebox):
    def lextok(self) -> 'parsernode|None':
        if (tok := self.gettabtok()) and tok.tabs == self.p.indent:
            self.next()
            return compound_stmt(self.p) or simple_stmts(self.p)

class vardef(statebox):
    def lextok(self) -> 'parsernode|None':
        if not (name := self.getidftok()): return
        if not (op := self.getoptok(':')): return
        if not (r := expression(self.p)): return

class assignment(statebox):
    def lextok(self) -> 'parsernode|None':
        pass
        
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

    def lextok(self) -> 'parsernode|None':
        if tok := self.getoptok(self.ops):
            return self.ops[tok.op](self.p)
        return assignment(self.p) or star_expressions(self.p)

class simple_stmts(statebox):

    @dataclass
    class node(parsernode):
        args:'list[parsernode]'

    def getstmts(self):
        while r := simple_stmt(self.p):
            yield r
            if self.getoptok(';'): self.next()
            else: break
        assert self.gettabtok(); return

    def lextok(self):
        assert (args := list(*self.getstmts()))
        return self.node(args)

class list_listcomp(statebox):
    tracking = False
    def lextok(self) -> 'parsernode|None':
        raise NotImplementedError
class tuple_group_genexp(statebox):
    tracking = False
    def lextok(self) -> 'parsernode|None':
        raise NotImplementedError
class dict_set_dictcomp_setcomp(statebox):
    tracking = False
    def lextok(self) -> 'parsernode|None':
        raise NotImplementedError

class strings(statebox):
    @dataclass
    class node(parsernode):
        strings:tuple[strtok]
    def getstrings(self):
        while tok := self.getstrtok(): yield tok
    def lextok(self) -> 'parsernode|None':
        if strings := (*self.getstrings(),):
            return self.node(strings)

class atom(statebox):

    @dataclass
    class identifier(parsernode):
        name:idftok

    @dataclass
    class bool_none(parsernode):
        op:optok

    @dataclass
    class number(parsernode):
        num:numtok

    @dataclass
    class ellipsis(parsernode):
        op:optok

    def lextok(self) -> 'parsernode|None':
        tok = self.gettok()
        if isinstance(tok, idftok):
            self.next(); return self.identifier(tok)
        elif isinstance(tok, optok):
            if tok.op == '...': return self.ellipsis(tok)
            elif tok.op in ('True','False','None'):
                self.next(); return self.bool_none(tok)
            elif tok.op == '[': return list_listcomp(self.p)
            elif tok.op == '(': return tuple_group_genexp(self.p)
            elif tok.op == '{': return dict_set_dictcomp_setcomp(self.p)
        elif isinstance(tok, numtok):
            self.next(); return self.number(tok)
        elif r := strings(self.p): return r

class genexp(statebox):
    tracking = False

    def lextok(self) -> 'parsernode|None':
        return None # TODO

class starred_expression(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        r:parsernode

    def lextok(self) -> 'parsernode|None':
        if op := self.getoptok('*'):
            self.next(); r = expression(self.p, parsererror)
            return self.node(op, r)

class kwarg(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        name:idftok
        r:parsernode

    def lextok(self) -> 'parsernode|None':
        if name := self.getidftok():
            self.next()
            assert (tok := self.getoptok('=')); self.next()
            assert (r := expression(self.p))
            return self.node(tok, name, r)

class argument(statebox):
    def lextok(self) -> 'parsernode|None':
        if r := starred_expression(self.p):
            return r
        elif r := assignment_expression(self.p) or expression(self.p):
            if self.getoptok('='): return
            return r

class kwarg_or_starred(statebox):
    def lextok(self) -> 'parsernode|None':
        if r := kwarg(self.p): return r
        elif r := starred_expression(self.p): return r

class kwarg_or_double_starred(statebox):
    @dataclass
    class node(parsernode):
        op:optok
        r:parsernode

    def lextok(self) -> 'parsernode|None':
        if r := kwarg(self.p): return r
        elif op := self.getoptok('**'):
            self.next(); r = expression(self.p, parsererror)
            return self.node(op, r)

class arguments(statebox):
    tracking = False

    @dataclass
    class node(parsernode):
        op:optok
        args:'list[parsernode]'

    def getargs(self):
        if self.getoptok(')'): self.next(); return
        for f in (argument, kwarg_or_starred, kwarg_or_double_starred):
            while arg := f(self.p):
                yield arg
                assert (tok := self.getoptok(',',')'))
                self.next()
                if tok.op == ')': return
        assert self.getoptok(')'); self.next()

    def lextok(self) -> 'parsernode|None':
        if op := self.getoptok('('):
            self.next()
            return self.node(op, list(self.getargs()))

class slice(statebox):

    @dataclass
    class node(parsernode):
        opA:optok
        opB:'optok|None'
        a:'parsernode|None'
        b:'parsernode|None'
        c:'parsernode|None'

    def lextok(self) -> 'parsernode|None':
        a = expression(self.p)
        if opA := self.getoptok(':'):
            self.next()
            b = expression(self.b)
            if opB := self.getoptok(':'):
                self.next()
                c = expression(self.b)
            else: c = None
            return self.node(opA, opB, a, b, c)

class slices(statebox):
    tracking = False

    @dataclass
    class node(parsernode):
        op:optok
        args:'list[parsernode]'

    def getslices(self):
        while r := slice(self.p) or named_expression(self.p):
            yield r
            assert (tok := self.getoptok(',',']'))
            self.next()
            if tok.op == ']': return
        assert (tok := self.getoptok(']')); self.next()

    def lextok(self) -> 'parsernode|None':
        if op := self.getoptok('['):
            self.next()
            r = self.node(op, list(self.getslices()))
            return r

class primary(statebox):

    @dataclass
    class attributeref(parsernode):
        op:optok
        a:parsernode
        name:idftok
    
    @dataclass
    class call(parsernode):
        op:optok
        a:parsernode
        arg:parsernode

    def lextok(self) -> 'parsernode|None':
        if a := atom(self.p):
            while tok := self.getoptok('.', '(', '['):
                if tok.op == '.':
                    self.next(); assert (name := self.getidftok())
                    self.next(); a = self.attributeref(tok, a, name)
                elif tok.op == '(':
                    assert (b := genexp(self.p) or arguments(self.p))
                    a = self.call(tok, a, b)
                elif tok.op == '[':
                    assert (b := slices(self.p))
                    a = self.call(tok, a, b)
            return a

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

class block(statebox):
    def lextok(self) -> 'parsernode|None':
        tok = self.gettok()
        if isinstance(tok, tabtok):
            assert tok.tabs > self.p.indent
            indent = self.p.indent
            self.p.indent = tok.tabs
            assert (r := statements(self.p))
            assert (tok := self.gettabtok())
            assert self.p.indent > tok.tabs
            assert indent >= tok.tabs
            if indent == tok.tabs: self.next()
            return r
        raise NotImplementedError

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

    class ifnode(parsernode):
        def __init__(self, op:optok, if_test:parsernode, *nodes:parsernode):
            self.op = op
            self.if_test = if_test
            self.nodes = nodes

    def getelifs_else(self):
        while op := self.getoptok('elif'):
            self.next(); assert (a := named_expression(self.p))
            assert self.getoptok(':'); self.next()
            yield self.elifnode(op, a, block(self.p, parserfail))
        if op := self.getoptok('else'):
            self.next()
            assert self.getoptok(':'); self.next()
            yield self.elsenode(op, block(self.p, parserfail))

    def lextok(self):
        if tok := self.getoptok('if'):
            self.next(); a = named_expression(self.p, parserfail)
            assert self.getoptok(':'); self.next()
            b = block(self.p, parserfail)
            return self.ifnode(tok, a, b, *self.getelifs_else)

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

    def lextok(self) -> 'parsernode|None':
        if t := self.getoptok(*self.ops):
            return self.ops[t.op](self.p)

