# cythonparser.py

from typing import Callable
from cythonlexer import lexer, lextok, optok, idftok, tabtok, numtok, strtok, badtok

class tabs:
    def __init__(self, p:'parser', *args):
        self.p = p
        self.args = args
    def __enter__(self):
        self.p.tabs(*self.args)
        self.tabnum = self.p.tabnum
        self.p.tabnum += 1
    def __exit__(self, *args): self.p.tabnum = self.tabnum

def withtabs(f:'Callable[[parser],parsenode]'):
    def _withtabs(p:'parser'):
        with tabs(p, f.__name__): return f(p)
    _withtabs.__name__ = f.__name__
    return _withtabs

class parsenode:
    def __init__(self, p:'parser'):
        raise parsererror(self.__class__.__name__, NotImplemented)

class parsererror(Exception): pass

class ignoreindent:
    def __init__(self, p:'parser'):
        self.p = p
    def __enter__(self):
        self.tracking = self.p.tracking_indent
        self.p.tracking_indent = False
    def __exit__(self, *args):
        self.p.tracking_indent = self.tracking

class trackindent:
    def __init__(self, p:'parser'):
        self.p = p
    def __enter__(self):
        self.tracking = self.p.tracking_indent
        self.p.tracking_indent = True
    def __exit__(self, *args):
        self.p.tracking_indent = self.tracking

class parser:
    def __init__(self, filepath:str):
        self.lexlist = list(lexer(filepath))
        self.tabnum = 0
        self.lexlist_len =  len(self.lexlist)
        self.lexidx = 0
        self.tracking_indent = False
        self.indent_level = 0

        with open('lexer.log', 'w') as f:
            print(*self.lexlist, file=f, sep='\n')
    
    def tabs(self, *args):
        print('  ' * self.tabnum + ' ', *args, self.lexidx, self.lexlist[self.lexidx])

    def getnext(self, t:'type[lextok]', match:bool=True):
        if self.lexidx >= self.lexlist_len:
            raise parsererror('getnext', 'hit-endmarker')
        
        tok = self.lexlist[self.lexidx]
        if match == isinstance(tok, t):
            self.tabs('getnext')
            self.lexidx += 1
            return tok
        raise parsererror('getnext', 'no-match', t.__name__, type(tok).__name__)

    def trynewline(self):
        tok:tabtok = self.getnext(tabtok)
        if tok.tabs == self.indent_level: return
        raise NotImplementedError('trynewline', 'indent/dendent', tok)

    def tryendmarker(self):
        if self.lexidx < self.lexlist_len:
            raise parsererror('tryendmarker', 'not-found')

    def tryidentifier(self):
        tok:idftok = self.getnext(idftok)
        return tok

    def tryinteger(self):
        tok:numtok = self.getnext(numtok)
        return tok

    def trystrings(self):
        idx = -1
        ret:'list[strtok]' = []
        try:
            while idx < (idx := self.lexidx):
                tok = self.getnext(strtok)
                ret.append(tok)
        except parsererror:
            self.lexidx = idx
            if ret: return ret
        raise parsererror('trystrings', 'none-found')

    def tryops(self, *ops:str, optional:bool=False):
        idx = self.lexidx
        tok:optok = self.getnext(optok)
        if tok.op in ops: return tok
        self.lexidx = idx
        if optional: return None
        raise parsererror('tryops', 'not-found', *ops)

    def trywhile(self, arg:Callable[['parser'],parsenode], min=0):
        ret:'list[parsenode]' = []
        with tabs(self, 'trywhile', arg.__name__):
            try:
                idx = -1
                while idx < (idx := self.lexidx):
                    tok = arg(self)
                    ret.append(tok)
            except parsererror as e:
                self.lexidx = idx
                self.tabs('caught', e)
                if len(ret) >= min: return ret
                raise parsererror('trywhile', 'too-few', len(ret))
            raise parsererror('trywhile', 'no-move')

    def tryor(self, *args:Callable[['parser'],parsenode], optional:bool=False):
        idx = self.lexidx
        with tabs(self, 'tryor', [arg.__name__ for arg in args]):
            for arg in args:
                try: return arg(self)
                except parsererror as e:
                    self.lexidx = idx
                    self.tabs('caught', e)
            if optional: return None
            raise parsererror('tryor', 'not-found')

    def tryoptional(self, arg:Callable[['parser'],parsenode]):
        idx = self.lexidx
        with tabs(self, 'tryor', arg.__name__):
            try: return arg(self)
            except parsererror as e:
                self.lexidx = idx
                self.tabs('caught', e)
            return None
