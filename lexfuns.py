from cythonlexer import optok
from cythonparser import parser, trackindent, ignoreindent, withtabs, parsenode, tabs, parsererror
from typing import Callable, Generator

def tryops(*args:str, optional:bool=False):
    def _tryops(p:parser):
        return p.tryops(*args, optional=optional)
    return _tryops

@withtabs
class file_input(parsenode):
    def __init__(self, p:parser):
        with trackindent(p):
            p.trynewline()
            self.stmts = p.trywhile(stmt)
            p.tryendmarker()

@withtabs
def stmt(p:parser):
    return p.tryor(compound_stmt, simple_stmt)

@withtabs
class simple_stmt(parsenode):
    def __init__(self, p:parser):
        self.stmts = [small_stmt(p)] + p.trywhile(post_stmt)
        p.tryops(';', optional=True)
        p.trynewline()

def post_stmt(p:parser):
    p.tryops(';')
    s = small_stmt(p)
    return s

@withtabs
def small_stmt(p:parser):
    return p.tryor(expr_stmt, del_stmt, pass_stmt, flow_stmt,
            import_stmt, global_stmt, nonlocal_stmt, assert_stmt)

@withtabs
class expr_stmt(parsenode):
    def __init__(self, p:parser):
        self.testlist_star_expr = testlist_star_expr(p)
        self.annassign = p.tryoptional(annassign)
        self.augassign_operator = p.tryoptional(augassign)
        self.assign_list = p.trywhile(assign_list)

@withtabs
class annassign(parsenode):
    def __init__(self, p:parser):
        p.tryops(':')
        self.type = test(p)
        self.assign = p.tryops('=', optional=True)
        if not self.assign:
            self.expr = None
            return
        self.expr = p.tryor(yield_expr, testlist_star_expr, optional=True)
        assert self.expr

@withtabs
class augassign(parsenode):
    ops = '+= -= *= @= /= %= &= |= ^= <<= >>= **= //='.split()
    def __init__(self, p:parser):
        self.op = p.tryops(self.ops)
        self.testlist = p.tryor(yield_expr, testlist, optional=True)
        assert self.testlist

class empty_assign(parsenode):
    def __init__(self, tok:optok): self.tok = tok

@withtabs
def assign_list(p:parser):
    tok = p.tryops('=')
    return p.tryor(yield_expr, testlist_star_expr, optional=True) or empty_assign(tok)

class yield_from(parsenode):
    def __init__(self, generator:'parsenode|None'):
        self.generator = generator
        assert generator

class yield_arg(parsenode):
    def __init__(self, arg:'parsenode|None'):
        self.arg = arg

@withtabs
def yield_expr(p:parser):
    p.tryops('yield')
    if tryops('from', optional=True):
        return yield_from(p.tryoptional(test))
    return yield_arg(p.tryoptional(testlist_star_expr))

@withtabs
class testlist_star_expr(parsenode):
    def __init__(self, p:parser):
        def getlist(p:parser):
            p.tryops(',')
            return p.tryor(test, star_expr)
        self.list = [p.tryor(test, star_expr)] + p.trywhile(getlist)

class del_stmt(parsenode): pass
class pass_stmt(parsenode): pass
class flow_stmt(parsenode): pass
class import_stmt(parsenode): pass
class global_stmt(parsenode): pass
class nonlocal_stmt(parsenode): pass
class assert_stmt(parsenode): pass

class operator(parsenode):
    def __init__(self, op:str, *args:'parsenode|None'):
        self.op = op
        self.args = args
        assert args.count(None) == 0

def expr_test(f:'Callable[[], tuple[Callable[[parser],parsenode],Callable[[parser],str]]]'):
    def _expr_test(p:parser):
        subop, getop = f()
        def expr_test_ops(p:parser):
            with tabs(p, f.__name__, 'ops'):
                return operator(getop(p), subop(p))
        with tabs(p, f.__name__):
            ret = subop(p)
            for node in p.trywhile(expr_test_ops):
                ret = operator(node.op, ret, *node.args)
            return ret
    return _expr_test

# atom ::= identifier | literal | enclosure
@withtabs
def atom(p:parser): return p.tryor(identifier, literal, enclosure)

@withtabs
class identifier(parsenode):
    def __init__(self, p:parser):
        self.name = p.tryidentifier()

# literal ::= stringliteral | bytesliteral | integer | floatnumber | imagnumber
#             | '...' | 'None' | 'True' | 'False'
@withtabs
def literal(p:parser):
    return p.tryor(stringliteral, bytesliteral, integer,
        boolliteral, floatnumber, imagnumber, ellipsis_op)

@withtabs
class stringliteral(parsenode):
    def __init__(self, p:parser):
        self.strings = p.trystrings()

@withtabs
class integer(parsenode):
    def __init__(self, p:parser):
        self.num = p.tryinteger()

@withtabs
class boolliteral(parsenode):
    def __init__(self, p:parser):
        tfn = p.tryops('True', 'False', 'None')
        if tfn == 'True': self.value = True
        elif tfn == 'False': self.value = False
        else: self.value = None

class bytesliteral(parsenode): pass
class floatnumber(parsenode): pass
class imagnumber(parsenode): pass

@withtabs
class ellipsis_op(parsenode):
    def __init__(self, p:parser):
        p.tryops('...')
        self.ellipsis = True

@withtabs
class enclosure(parsenode): pass
@withtabs
class arglist(parsenode): pass

@withtabs
class call(parsenode):
    def __init__(self, p:parser):
        p.tryops('(')
        with ignoreindent(p):
            self.args = p.tryoptional(arglist)
        p.tryops(')')

class sliceop(parsenode):
    def __init__(self, *args:'parsenode|None'):
        self.args = args

@withtabs
def subscript(p:parser):
    t1 = p.tryoptional(test)
    c1 = p.tryoptional(tryops(':'))
    if not c1:
        if t1: return t1
        raise parsererror('subscript')
    t2 = p.tryoptional(test)
    c2 = p.tryoptional(tryops(':'))
    t3 = c2 and p.tryoptional(test)
    return sliceop(t1,t2,t3)

def subscriptlist(p:parser):
    p.tryops(',')
    return subscript(p)

@withtabs
class subscription(parsenode):
    def __init__(self, p:parser):
        p.tryops('[')
        with ignoreindent(p):
            ss = p.tryoptional(subscript)
            assert ss
            self.args = [ss] + p.trywhile(subscriptlist)
            p.tryops(',', optional=True)
        p.tryops(']')

@withtabs
class attributeref(parsenode):
    def __init__(self, p:parser):
        p.tryops('.')
        self.name = p.tryidentifier()

@withtabs
def trailer(p:parser): return p.tryor(call, subscription, attributeref)

@withtabs
def atom_expr(p:parser):
    ret = atom(p)
    for op in p.trywhile(trailer):
        ret = operator('trailer', ret, op)
    return ret

@withtabs
def power(p:parser):
    ret = atom_expr(p)
    if p.tryops('**', optional=True):
        return operator('**', ret, p.tryoptional(factor))
    return ret

@withtabs
def factor(p:parser):
    ops = p.trywhile(tryops('+','-','~'))
    ret = power(p)
    ops.reverse()
    for op in ops: ret = operator(op, ret)
    return ret

@expr_test
def term(): return factor, tryops('*','@','/','%','//')
@expr_test
def arith_expr(): return term, tryops('+', '-')
@expr_test
def shift_expr(): return arith_expr, tryops('<<', '>>')
@expr_test
def and_expr(): return shift_expr, tryops('&')
@expr_test
def xor_expr(): return and_expr, tryops('^')
@expr_test
def expr(): return xor_expr, tryops('|')
@expr_test
def comparison(): return expr, comparison_ops
def comparison_ops(p:parser):
    if ret := p.tryops('<','>','==','>=','<=','<>','!=','in', optional=True):
        return ret
    elif ret := p.tryops('is'):
        if p.tryops('not'):
            return optok(ret.info, 'is not')
        return ret
    elif ret := p.tryops('not'):
        if p.tryops('in'):
            return optok(ret.info, 'not in')
        raise parsererror('comparison', 'no-in-after-not')
    raise parsererror('comparison', 'no-op')

@withtabs
def not_test(p:parser):
    oddnots = 1 & len(p.trywhile(tryops('not')))
    _comparison = comparison(p)
    return operator('not', _comparison) if oddnots else _comparison

@expr_test
def and_test(): return not_test, tryops('and')
@expr_test
def or_test(): return and_test, tryops('or')

@withtabs
def test(p:parser): return p.tryor(ternary, lambdef)

@withtabs
def ternary(p:parser):
    _or_test = or_test(p)
    if p.tryoptional(tryops('if')):
        _if_test = or_test(p)
        p.tryops('else')
        _else_test = test(p)
        return operator('ternary', _or_test, _if_test, _else_test)
    else: return _or_test

@withtabs
class lambdef(parsenode): pass

class star_expr(parsenode): pass
class testlist(parsenode): pass

# compound_stmt ::= if_stmt | while_stmt | for_stmt | try_stmt | with_stmt | funcdef | classdef | decorated | async_stmt
@withtabs
def compound_stmt(p:parser):
    return p.tryor(if_stmt, while_stmt, for_stmt, try_stmt, with_stmt, funcdef, classdef, decorated, async_stmt)

# if_stmt ::= 'if' namedexpr_test ':' suite elif_stmt* [else_stmt]
@withtabs
class if_stmt(parsenode):
    def __init__(self, p:parser):
        p.tryops('if')
        self.if_test = p.tryoptional(namedexpr_test)
        p.tryops(':')
        self.suite = p.tryoptional(suite)
        assert self.if_test or self.suite
        self.elif_stmts = p.trywhile(elif_stmt)
        self.else_stmt = p.tryoptional(else_stmt)

# elif_stmt ::= 'elif' namedexpr_test ':' suite
@withtabs
class elif_stmt(parsenode):
    def __init__(self, p:parser):
        p.tryops('elif')
        self.if_test = p.tryoptional(namedexpr_test)
        p.tryops(':')
        self.suite = p.tryoptional(suite)
        assert self.if_test or self.suite

# else_stmt ::= 'else' ':' suite
@withtabs
class else_stmt(parsenode):
    def __init__(self, p:parser):
        p.tryops('else')
        p.tryops(':')
        self.suite = p.tryoptional(suite)
        assert self.suite

class while_stmt(parsenode): pass
class for_stmt(parsenode): pass
class try_stmt(parsenode): pass
class with_stmt(parsenode): pass
class funcdef(parsenode): pass
class classdef(parsenode): pass
class decorated(parsenode): pass
class async_stmt(parsenode): pass

# suite ::= simple_stmt | NEWLINE INDENT stmt+ DEDENT
class suite(parsenode): pass

class namedexpr(parsenode):
    def __init__(self, identifier:test, expr:'parsenode|None'):
        self.identifier = identifier
        self.expr = expr
        assert expr

# namedexpr_test ::= test [':=' test]
@withtabs
def namedexpr_test(p:parser):
    identifier_expr = test(p)
    op = p.tryops(':=', optional=True)
    if op: return namedexpr(identifier_expr, p.tryoptional(test))
    return identifier_expr
