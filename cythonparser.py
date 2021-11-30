# cythonparser.py

from dataclasses import dataclass
from typing import Generator
from cythonlexer import *

class parserfail(Exception): pass
class parsernode: pass

class parser:
    def __init__(self, filename:str):
        self.toks = list(lexer(filename))
        self.ntoks = len(self.toks)
        self.ntabs = 0
        self.idx = 0

class statebox:

    def __init__(self, p:parser): self.p = p
    def __new__(cls, p:parser, err:'type[Exception]|None'=None):
        cls.__init__(self := super().__new__(cls), p)
        idx = self.p.idx
        ntabs = self.p.ntabs
        self.p.ntabs += 1
        try: r = self.lextok()
        finally: self.p.ntabs = ntabs
        if r: return r
        elif err: raise err
        self.p.idx = idx

    def gettok(self): return self.p.toks[self.p.idx]
    
    def next(self): self.p.idx += 1

    def lextok(self) -> 'parsernode|None':
        raise NotImplementedError

    def getoptok(self, *ops:str):
        if isinstance(tok := self.gettok(), optok):
            if not ops or tok.op in ops: return tok
    def getidftok(self):
        if isinstance(tok := self.gettok(), idftok):
            return tok
    def gettabtok(self):
        if isinstance(tok := self.gettok(), tabtok):
            return tok
    def getnumtok(self):
        if isinstance(tok := self.gettok(), numtok):
            return tok
    def getstrtok(self):
        if isinstance(tok := self.gettok(), strtok):
            return tok
    def getbadtok(self):
        if isinstance(tok := self.gettok(), badtok):
            return tok
    def getendtok(self):
        if isinstance(tok := self.gettok(), endtok):
            return tok

    def optional(self, arg:'statebox') -> 'parsernode|None':
        idx = self.p.idx
        if r := arg(self.p): return r
        self.p.idx = idx
        return None

    def options(self, *args:'statebox') -> 'parsernode|None':
        idx = self.p.idx
        for arg in args:
            if r := arg(self.p): return r
            self.p.idx = idx

    def rep0(self, arg:'statebox') -> Generator[parsernode,None,None]:
        idx = -1
        while True:
            assert idx < self.p.idx
            idx = self.p.idx
            if r := arg(self.p): yield r
            else:
                self.p.idx = idx
                return

    def rep1(self, arg:'statebox') -> Generator[parsernode,None,None]:
        idx = self.p.idx
        assert (r := arg(self.p)); yield r
        while True:
            assert idx < self.p.idx
            idx = self.p.idx
            if r := arg(self.p): yield r
            else:
                self.p.idx = idx
                return
