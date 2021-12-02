# cyparser.py
from typing import Callable, Literal
from cytree import *

class parser:

    def __init__(self, filename:str, file:str):
        self.filename = filename
        self.lexer = lexer(file)
        self.toks = list(self.lexer)
        self.ntoks = len(self.toks)
        self.tmap:'dict[tuple[int,int],tree_range|Literal[True]]' = {}
        self.indent = 0
        self.indent_tracking = True
        self.tok = self.toks[0]

    def syntax_error(self, msg:str):
        print(f'File "{self.filename}", line {self.tok.lnum}')
        print(self.lexer.lines[self.tok.lnum])
        print(' ' * self.tok.lidx + '^')
        print(msg)
        exit(-1)

    def rule(self, rule:'Callable[[parser],tree_node|None]'):
        tup = self.tok.tidx, id(rule)
        if ret := self.tmap.get(tup):
            if ret is True: return
            self.tok = ret.end
            return ret
        self.tmap[tup] = True
        tok = self.tok
        if ret := rule(self):
            if isinstance(ret, tree_range): ret = ret.node
            self.tmap[tup] = ret = tree_range(ret, tok, self.tok)
            return ret
        self.tok = tok

    def rules(self, *rules:'Callable[[parser],tree_node|None]', err:'str|None'=None):
        for rule in rules:
            if r := self.rule(rule):
                return r
        if err: self.syntax_error(err)

    def next(self):
        self.tok = self.toks[self.tok.tidx+1]
        if self.indent_tracking: return
        self.nexttok(tabtok)

    def gettok(self, *lexs:type[lextok], ops:'set[str]|None'=None, err:'str|None'=None):
        rlex = None
        for lex in lexs:
            if isinstance(self.tok, lex):
                rlex = lex; break
        if rlex and (not ops or self.tok.str in ops):
            return self.tok
        elif err: self.syntax_error(err)

    def nexttok(self, *lexs:type[lextok], ops:'set[str]|None'=None, err:'str|None'=None):
        if tok := self.gettok(*lexs, ops=ops, err=err):
            self.next()
            return tok

class indent_tracking:
    def __init__(self, p:parser, indented_state:bool):
        self.p = p
        self.indented_state = indented_state
    def __enter__(self):
        self.prev_state = self.p.indent_tracking
        self.p.indent_tracking = self.indented_state
    def __exit__(self, *args):
        self.p.indent_tracking = self.prev_state
