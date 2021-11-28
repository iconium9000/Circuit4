# lexer.py
import sys
import re
from typing import Callable, Generator
from dataclasses import dataclass

@dataclass
class matchinfo:
    string:str
    filename:str
    lidx:int
    start:int
    end:int
    line:str

class charlist:

    def __init__(self, filename:str, file:str):
        self.filename = filename
        file = '\n' + file + '\n\n\\'
        self.fidx = 0
        self.file = str()
        self.lines:'list[str]' = []
        self.lidx = 0

        fidx = 0
        self.ls_fidxs:'list[int]' = []
        self.le_fidxs:'list[int]' = []
        for line in file.split('\n'):
            self.ls_fidxs.append(fidx)
            if line and line[-1] == '\\':
                line = line[:-1]
                fidx += len(line)
                tfidx = fidx
                self.file += line
            else:
                tfidx = fidx + len(line)
                self.file += line + '\n'
                fidx = tfidx+1
            self.le_fidxs.append(tfidx)
            self.lines.append(line)

    def match(self, pattern:re.Pattern[str]):
        m = pattern.match(self.file, self.fidx)
        if not m: return None
        start,end = m.span()
        self.fidx = end
        while start > self.le_fidxs[self.lidx]:
            self.lidx += 1
        ls_fidx = self.ls_fidxs[self.lidx]
        string = self.file[start:end]
        start -= ls_fidx
        end -= ls_fidx
        line = self.lines[self.lidx]
        return matchinfo(string,self.filename,self.lidx,start,end,line)

nwlpat = re.compile(r'(\#[^\n]*| |\n)*\n')
tabpat = re.compile(r' *')
spcpat = re.compile(r' +')
idfpat = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
numpat = re.compile(r'0(x|X)[0-9a-fA-F]+|0(b|B)[01]+|0[0-7]*|[0-9]+')
strpat = re.compile(r'\"(\\\"|[^\"])*\"|\'(\\\'|[^\'])*\'')
badpat = re.compile(r'.')

opslist = (
    '| & / { = <<= < - @= ^ } := &= '
    '% [ ** >> >>= |= : == @ *= <> -> '
    '%= **= ~ //= != . > -= ; , // ] '
    '* /= ... ) ( ^= << <= >= += +'.split())
opslist.sort(key=lambda s : len(s))
opslist.reverse()
opslist = ['\\' + '\\'.join(op) for op in opslist]
opspat = re.compile('|'.join(opslist))

keywords = set(
    'def del pass break continue return raise from import '
    'as global nonlocal assert if while lambda class '
    'for in else elif finally with or and not None True False'.split())

class tabs:
    num = 0

    @classmethod
    def now(cls): return '|' * cls.num
    def __init__(self, *args): self.args = args
    def __enter__(self):
        print(self.now() + 'tabs', *self.args)
        tabs.num += 1
    def __exit__(self, *args): tabs.num -= 1

def withtabs(c:'Callable[[parser],parsenode]'):
    def _withtabs(p:'parser'):
        with tabs(c.__name__):
            return c(p)
    return _withtabs

class parsenode:
    def __init__(self, p:'parser'):
        raise p.parsefail(self.__class__.__name__, NotImplemented)

class parsefail(Exception): pass

@dataclass
class lextok: info:matchinfo

@dataclass
class optok(lextok): op:str

@dataclass
class inftok(lextok): name:str

@dataclass
class tabtok(lextok): tabs:int

@dataclass
class numtok(lextok): num:str

@dataclass
class strtok(lextok): string:str

@dataclass
class badtok(lextok): pass

class parser:
    @staticmethod
    def lexer(filepath:str):
        with open(filepath, 'r') as f:
            file = f.read()
        chars = charlist(filepath, file)
        idx = -1
        while chars.fidx > idx:
            idx = chars.fidx
            if m := chars.match(strpat):
                yield strtok(m, m.string)
            elif chars.match(nwlpat):
                info = chars.match(tabpat)
                yield tabtok(info, len(info.string))
            elif chars.match(spcpat): pass
            elif m := chars.match(idfpat):
                tok = optok if m.string in keywords else inftok
                yield tok(info, m.string)
            elif m := chars.match(numpat): yield numtok(m, m.string)
            elif m := chars.match(opspat): yield optok(m, m.string)
            elif m := chars.match(badpat): yield badtok(m)
            else: return
        raise Exception('nomove')

    def __init__(self, filepath:str):
        self.lexlist = list(self.lexer(filepath))
        self.lexlist_len =  len(self.lexlist)
        self.lexidx = 0
        for lex in self.lexlist:
            print(lex)

    def parsefail(self, *args:str):
        print(tabs.now() + 'fail', *args, self.lexlist[self.lexidx])
        return parsefail(*args)

    def trynewline(self):
        raise NotImplementedError('trynewline')

    def tryindent(self):
        raise NotImplementedError('tryindent')

    def trydedent(self):
        raise NotImplementedError('trydedent')

    def trackindent(self):
        raise NotImplementedError('trackindent')
    
    def ignoreindent(self):
        raise NotImplementedError('trackindent')

    def tryendmarker(self):
        if self.lexidx < self.lexlist_len:
            raise self.parsefail('tryendmarker')

    def tryops(self, *ops:str, optional:bool=False):
        if self.lexidx >= self.lexlist_len:
            raise self.parsefail('tryops', 'endmarker')
        tok = self.lexlist[self.lexidx]
        if not isinstance(tok, optok):
            raise self.parsefail('tryops', 'not-op')
        elif tok.op in ops:
            self.lexidx += 1
            return tok
        if optional: return None
        raise self.parsefail('tryops', 'not-found')

    def trywhile(self, arg:Callable[['parser'],parsenode], min=0):
        idx = -1
        ret:'list[parsenode]' = []
        while idx < (idx := self.lexidx) and (argret := self.tryoptional(arg)):
            ret.append(argret)
        if argret: raise self.parsefail('trywhile', 'nomove')
        elif len(ret) < min:
            raise self.parsefail('trywhile', 'retmin', len(ret), min)
        return ret

    def tryor(self, *args:Callable[['parser'],parsenode], optional:bool=False):
        idx = self.lexidx
        for arg in args:
            try: return arg(self)
            except parsefail: self.lexidx = idx
        if optional: return None
        raise self.parsefail('tryor')

    def tryoptional(self, arg:Callable[['parser'],parsenode]):
        idx = self.lexidx
        try: return arg(self)
        except parsefail: self.lexidx = idx
        return None

def tryops(*args:str, optional:bool=False):
    def _tryops(p:parser):
        return p.tryops(*args, optional=optional)
    return _tryops

@withtabs
class file_input(parsenode):
    def __init__(self, p:parser):
        self.stmts = p.trywhile(stmt)
        p.tryendmarker()

@withtabs
def stmt(p:parser):
    return p.tryor(simple_stmt, compound_stmt)

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
            self.error = False
            return
        self.expr = p.tryor(yield_expr, testlist_star_expr, optional=True)
        self.error = not self.expr

@withtabs
class augassign(parsenode):
    ops = '+= -= *= @= /= %= &= |= ^= <<= >>= **= //='.split()
    def __init__(self, p:parser):
        self.op = p.tryops(self.ops)
        self.testlist = p.tryor(yield_expr, testlist, optional=True)
        self.error = not self.testlist

class empty_assign(parsenode):
    def __init__(self, tok:optok): self.tok = tok

@withtabs
def assign_list(p:parser):
    tok = p.tryops('=')
    return p.tryor(yield_expr, testlist_star_expr, optional=True) or empty_assign(tok)

class yield_from(parsenode):
    def __init__(self, generator:'parsenode|None'):
        self.generator = generator
        self.error = not generator

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
    def __init__(self, op:str, *args:parsenode):
        self.op = op
        self.args = args

def expr_test(f:'Callable[[], tuple[Callable[[parser],parsenode],Callable[[parser],str]]]'):
    def _expr_test(p:parser):
        subop, getop = f()
        def _tryops(p:parser): return operator(getop(p), subop(p))
        with tabs(f.__name__):
            ret = subop(p)
            for node in p.trywhile(_tryops):
                ret = operator(node.op, ret, *node.args)
            return ret
    return _expr_test

@withtabs
class atom(parsenode): pass

@withtabs
class arglist(parsenode): pass

@withtabs
class call(parsenode):
    def __init__(self, p:parser):
        p.tryops('(')
        p.ignoreindent()
        self.args = p.tryoptional(arglist)
        p.trackindent()
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
        raise p.parsefail('subscript')
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
        p.ignoreindent()
        ss = p.tryoptional(subscript)
        self.error = not ss
        self.args = [ss] + p.trywhile(subscriptlist)
        p.tryops(',', optional=True)
        p.trackindent()
        p.tryops(']')

@withtabs
class attributeref(parsenode): pass


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
        return operator('**', ret, factor(p))

@withtabs
def factor(p:parser):
    ops = p.trywhile(tryops('+','-','~'))
    ret = power(p)
    ops.reverse()
    for op in ops:
        ret = operator('factor' + op, ret)
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
def comparison():
    def _tryops(p:parser):
        if ret := p.tryops('<','>','==','>=','<=','<>','!=','in', optional=True):
            return ret
        elif ret := p.tryops('is'):
            if p.tryops('not'):
                return optok(ret.info, 'is not')
            return ret
        elif ret := p.tryops('not'):
            if p.tryops('in'):
                return optok(ret.info, 'not in')
            raise p.parsefail('comparison', 'no-in-after-not')
        raise p.parsefail('comparison', 'no-op')
    return expr, _tryops

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

class compound_stmt(parsenode): pass

def main(filepath:str):
    p = parser(filepath)
    try: file_input(p)
    except parsefail: pass

if __name__ == "__main__":

    main(*sys.argv[1:])
