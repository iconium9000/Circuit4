# cythonparser.py
from cythonlexer import *

class parser:
    def __init__(self, filename:str):
        self.toks = list(lexer(filename))
        self.ntoks = len(self.toks)
        self.idx = 0
        self.tok = self.toks[self.idx]
        self.indent = 0
        self.tracking = True

class statebox:
    tracking = True

    def __init__(self, p:parser, syntax=False): self.p = p
    def __new__(cls, p:parser, syntax=False):
        cls.__init__(self := super().__new__(cls), p)
        idx = p.idx
        tok = self.p.tok = p.toks[idx]
        if cls.tracking:
            r = self.lextok()
        else:
            tracking = p.tracking
            p.tracking = False
            r = self.lextok()
            p.tracking = tracking
        if r: return r
        p.idx = idx
        self.p.tok = tok
        self.assert_syntax(not syntax)

    def next(self):
        self.p.idx += 1
        self.p.tok = self.p.toks[self.p.idx]
        if self.p.tracking: return
        self.tabtok_next()

    def assert_syntax(self, arg:bool):
        if arg: return
        info = self.p.tok.info
        print(f'File "{info.filename}", line {info.lidx}')
        print(info.line)
        print(' ' * info.start + '^')
        print('invalid syntax')
        exit(-1)

    def lextok(self) -> 'lextok|None':
        self.assert_syntax(False)

    def optok(self,*ops:str):
        if isinstance(self.p.tok, optok):
            if not ops or self.p.tok.op in ops:
                return self.p.tok
    def optok_next(self,*ops:str):
        if isinstance(tok := self.p.tok, optok):
            if not ops or tok.op in ops:
                self.next()
                return tok

    def idftok(self):
        if isinstance(self.p.tok, idftok):
            return self.p.tok
    def idftok_next(self):
        if isinstance(tok := self.p.tok, idftok):
            self.next()
            return tok

    def tabtok(self):
        if isinstance(self.p.tok, tabtok):
            return self.p.tok
    def tabtok_next(self):
        if isinstance(tok := self.p.tok, tabtok):
            self.next()
            return tok
            
    def numtok(self):
        if isinstance(self.p.tok, numtok):
            return self.p.tok
    def numtok_next(self):
        if isinstance(tok := self.p.tok, numtok):
            self.next()
            return tok

    def strtok(self):
        if isinstance(self.p.tok, strtok):
            return self.p.tok
    def strtok_next(self):
        if isinstance(tok := self.p.tok, strtok):
            self.next()
            return tok
            
    def badtok(self):
        if isinstance(self.p.tok, badtok):
            return self.p.tok
    def badtok_next(self):
        if isinstance(tok := self.p.tok, badtok):
            self.next()
            return tok
            
    def endtok(self):
        if isinstance(self.p.tok, endtok):
            return self.p.tok
    def endtok_next(self):
        if isinstance(tok := self.p.tok, endtok):
            self.next()
            return tok
            
