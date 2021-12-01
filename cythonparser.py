# cythonparser.py
from cythonlexer import *

class parser:
    def __init__(self, filename:str):
        self.toks = list(lexer(filename))
        self.ntoks = len(self.toks)
        self.idx = 0
        self.tok = self.toks[self.idx]
        self.rmap:'dict[tuple[int,int],lextok]' = {}
        self.indent = 0
        self.tracking = True

    def syntax_error(self):
        info = self.tok.info
        print(f'File "{info.filename}", line {info.lidx}')
        print(info.line)
        print(' ' * info.start + '^')
        print('invalid syntax')
        exit(-1)

class stoptracking:
    def __init__(self, p:parser):
        self.p = p
    def __enter__(self):
        self.tracking = self.p.tracking
        self.p.tracking = False
    def __exit__(self, *args):
        self.p.tracking = self.tracking

class statebox:
    def __init__(self, p:parser, syntax=False): self.p = p
    def __new__(cls, p:parser, syntax=False):
        if (tup := (idx := p.idx, id(cls))) in p.rmap:
            if r_idx_tok := p.rmap[tup]:
                r,p.idx,p.tok = r_idx_tok
                return r
            elif syntax: p.syntax_error()
            else: return
        else: tok = p.tok
        cls.__init__(self := super().__new__(cls), p)
        if r := self.lextok():
            p.rmap[tup] = r,self.p.idx,self.p.tok; return r
        p.rmap[tup],p.idx,self.p.tok = None,idx,tok
        if syntax: self.p.syntax_error()

    def next(self):
        self.p.idx += 1
        self.p.tok = self.p.toks[self.p.idx]
        if self.p.tracking: return
        self.tabtok_next()

    def lextok(self) -> 'lextok|None':
        print(self.__class__.__name__)
        self.p.syntax_error()

    def optok(self, *ops:str, syntax=False):
        if isinstance(self.p.tok, optok):
            if not ops or self.p.tok.op in ops:
                return self.p.tok
        if syntax: self.p.syntax_error()

    def optok_next(self, *ops:str, syntax=False):
        if isinstance(tok := self.p.tok, optok):
            if not ops or tok.op in ops:
                self.next()
                return tok
        if syntax: self.p.syntax_error()

    def idftok(self, syntax=False):
        if isinstance(self.p.tok, idftok):
            return self.p.tok
        elif syntax: self.p.syntax_error()

    def idftok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, idftok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()

    def tabtok(self, syntax=False):
        if isinstance(self.p.tok, tabtok):
            return self.p.tok
        elif syntax: self.p.syntax_error()

    def tabtok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, tabtok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()
            
    def numtok(self, syntax=False):
        if isinstance(self.p.tok, numtok):
            return self.p.tok
        elif syntax: self.p.syntax_error()
    def numtok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, numtok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()

    def strtok(self, syntax=False):
        if isinstance(self.p.tok, strtok):
            return self.p.tok
        elif syntax: self.p.syntax_error()
    def strtok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, strtok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()
    def badtok(self, syntax=False):
        if isinstance(self.p.tok, badtok):
            return self.p.tok
        elif syntax: self.p.syntax_error()
    def badtok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, badtok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()
            
    def endtok(self, syntax=False):
        if isinstance(self.p.tok, endtok):
            return self.p.tok
        elif syntax: self.p.syntax_error()
    def endtok_next(self, syntax=False):
        if isinstance(tok := self.p.tok, endtok):
            self.next()
            return tok
        elif syntax: self.p.syntax_error()
