from cythonlexer import *
import sys

class parser:
    def __init__(self, filename:str):
        self.toks = list(lexer(filename))
        self.numtoks = len(self.toks)
        self.idx = 0
        self.ntabs = 0

        self.bnf_dict = {}
        self.stmt_stack = []
        self.stmt = []

    def tabs(self, *args):
        print('  ' * self.ntabs + ' ', *args)

    def tok(self): return self.toks[self.idx]
    def next(self):
        self.idx += 1
        return self.toks[self.idx]

class parsererror(Exception): pass
class parserfail(Exception): pass

class statebox:
    def __init__(self, p:parser):
        # p.tabs('init', self.__class__.__name__)
        self.p = p
        idx = p.idx
        tabs = p.ntabs
        p.ntabs += 1
        try: self.lextok()
        except parsererror as e:
            p.idx = idx
            # p.tabs('error', p, idx)
            raise parsererror(e)
        finally:
            p.ntabs = tabs

    def lextok(self):
        tok = self.p.tok()
        if isinstance(tok, optok): self.optok(tok)
        elif isinstance(tok, idftok): self.idftok(tok)
        elif isinstance(tok, tabtok): self.tabtok(tok)
        elif isinstance(tok, numtok): self.numtok(tok)
        elif isinstance(tok, strtok): self.strtok(tok)
        elif isinstance(tok, endtok): self.endtok(tok)
        else: self.badtok(tok)

    def optok(self, t:optok): raise parsererror('optok')
    def idftok(self, t:idftok): raise parsererror('idftok')
    def tabtok(self, t:tabtok): raise parsererror('tabtok')
    def numtok(self, t:numtok): raise parsererror('numtok')
    def strtok(self, t:strtok): raise parsererror('strtok')
    def badtok(self, t:badtok): raise parsererror('badtok')
    def endtok(self, t:endtok): raise parsererror('endtok')

    def getoptok(self, *ops:str):
        tok = self.p.tok()
        if not isinstance(tok, optok): return None
        elif not ops or tok.op in ops: return tok
        else: return None
    def getidftok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, idftok) else None
    def gettabtok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, tabtok) else None
    def getnumtok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, numtok) else None
    def getstrtok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, strtok) else None
    def getbadtok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, badtok) else None
    def getendtok(self):
        tok = self.p.tok()
        return tok if isinstance(tok, endtok) else None

    def push_stack(self, name:str):
        stmt = [name]
        self.p.stmt.append(stmt)
        self.p.stmt_stack.append(self.p.stmt)
        self.p.stmt = stmt

    def pop_stack(self):
        stmt = self.p.stmt
        self.p.stmt = self.p.stmt_stack.pop()
        return stmt

    def pop_stmt(self):
        return self.p.stmt.pop()

    def push(self, *args):
        self.p.stmt.append(args)

    def pop(self):
        return self.p.stmt.pop()

class ENDMARKER(statebox):
    def endtok(self, t): return

class file(statebox):
    def tabtok(self, t):
        try:
            while statement(self.p): pass
        except parsererror: pass
        self.p.next()
        ENDMARKER(self.p)

class statement(statebox):
    def tabtok(self, t:tabtok):
        assert t.tabs == 0

        self.p.next()
        if not (idf := self.getidftok()):
            raise parsererror
        
        assert self.p.bnf_dict.get(idf.name) is None

        assert isinstance(colop := self.p.next(), optok)
        assert colop.op == ':'

        self.p.next()
        try: compound_stmt(self.p)
        except parsererror: simple_stmt(self.p)

        self.p.bnf_dict[idf.name] = self.pop_stack()

class compound_stmt(statebox):
    def lextok(self):
        self.push_stack('or')
        while tok := self.gettabtok():
            if tok.tabs == 0: return
            self.p.next()
            if not self.getoptok('|'): return
            self.p.next()
            simple_stmt(p)
        raise parsererror('not-tabtok')

class simple_stmt(statebox):
    def lextok(self):

        self.push_stack('or')
        self.push_stack('lst')
        try:
            while not isinstance(tok := self.p.tok(), (tabtok, endtok, badtok)):
                if isinstance(tok, optok) and tok.op in (']', ')'):
                    return
                atom(self.p)
        finally:
            self.pop_stack()
            self.pop_stack()

class atom(statebox):
    def optok(self, t:optok):
        self.p.next()
        try:
            if t.op == '(': return group_stmt(p)
            elif t.op == '[': return optional_stmt(p)
            elif t.op == '!': return exclusion(p)
            elif t.op == '&': return endswith(p)
            elif t.op == '?': return question(p)
            elif t.op == '*': return rep0(p)
            elif t.op == '+': return rep1(p)
            elif t.op == '|': return or_stmt(p)
            elif t.op == '.': return dot_stmt(p)
            elif t.op == '~': return tilde_stmt(p)
        except parsererror as e:
            raise parserfail(e)
        raise NotImplementedError()
    def idftok(self, t:idftok):
        self.push('idf', t.name)
        self.p.next()
    def numtok(self, t:numtok):
        self.push('num', t.name)
        self.p.next()
    def strtok(self, t:strtok):
        self.push('op', t.string)
        self.p.next()

class endswith(statebox):
    def lextok(self):
        self.push_stack('endswith')
        try: atom(self.p)
        finally: self.pop_stack()

class question(statebox):
    def lextok(self):
        self.push('question', self.pop())

class rep0(statebox):
    def lextok(self):
        self.push('rep0', self.pop())

class rep1(statebox):
    def lextok(self):
        self.push('rep1', self.pop())

class or_stmt(statebox):
    def lextok(self):
        self.pop_stack()
        self.push_stack('lst')

class dot_stmt(statebox):
    def lextok(self):
        a1 = self.pop()
        self.push_stack('lst')
        try: atom(self.p)
        finally:
            self.push(a1)
            self.pop_stack()

class group_stmt(statebox):
    def lextok(self):
        self.push_stack('lst')
        try:
            simple_stmt(self.p)
            assert self.getoptok(')')
            self.p.next()
        finally:
            self.pop_stack()

class optional_stmt(statebox):
    def lextok(self):
        self.push_stack('optional')
        try:
            simple_stmt(self.p)
            assert self.getoptok(']')
            self.p.next()
        finally:
            self.pop_stack()

class exclusion(statebox):
    def lextok(self):
        self.push_stack('exclusion')
        try: atom(self.p)
        finally:
            self.pop_stack()

class tilde_stmt(statebox):
    def lextok(self):
        a1 = self.pop()
        self.push_stack('tilde')
        self.push(a1)
        try: atom(self.p)
        finally:
            self.pop_stack()
def getlist(args):
    if isinstance(args, str): return args, True
    elif not args: return '', True
    elif len(args) == 1: return getlist(args[0])
    elif len(args) > 2: return [getlist(arg)[0] for arg in args], False
    arg0, is0str = getlist(args[0])
    arg1, is1str = getlist(args[1])
    if args[0] in ('or','lst'): return arg1, is1str
    elif is0str and is1str: return arg0 + ' ' + arg1, True
    return (arg0, arg1), False

def recprint(args, tab=''):
    args, isstr = getlist(args)
    if isstr:
        print(tab + args)
        return
    recprint(args[0], tab)
    for arg in args[1:]:
        recprint(arg, tab + '  ')

if __name__ == '__main__':
    p = parser(sys.argv[1])
    file(p)

    for symbol in p.bnf_dict.items():
        recprint(symbol)
