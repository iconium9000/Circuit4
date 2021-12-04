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
            self.tok = ret.next_tok
            return ret
        self.tmap[tup] = True
        tok = self.tok
        if ret := rule(self):
            if isinstance(ret, tree_range): ret = ret.node
            self.tmap[tup] = ret = tree_range(ret, tok, self.tok)
            return ret
        self.tok = tok

    def rule_err(self, rule:'Callable[[parser],tree_node|None]', err:str):
        return self.rule(rule) or self.syntax_error(err)

    def next(self):
        tok = self.tok
        self.tok = self.toks[self.tok.tidx+1]
        if not self.indent_tracking:
            self.nexttok(tabtok)
        return tok

    def gettok(self, *lexs:type[lextok], err:'str|None'=None):
        for lex in lexs:
            if isinstance(self.tok, lex):
                return self.tok
        if err: self.syntax_error(err)

    def nexttok(self, lex:type[lextok], err:'str|None'=None):
        if isinstance(self.tok, lex):
            return self.next()
        if err: self.syntax_error(err)

    def nextop(self, ops:set[str], err:'str|None'=None):
        if isinstance(tok := self.tok, opstok) and tok.str in ops:
            self.next()
            return tok
        if err: self.syntax_error(err)


def todo(r:'Callable[[parser],tree_node|None]'):
    def _r(p:parser) -> 'tree_node|None':
        p.syntax_error(f'"{r.__name__}" is Not Implemented')
    _r.__name__ = r.__name__
    return _r

class indent_tracking:
    def __init__(self, p:parser, indented_state:bool):
        self.p = p
        self.indented_state = indented_state
    def __enter__(self):
        self.prev_state = self.p.indent_tracking
        self.p.indent_tracking = self.indented_state
    def __exit__(self, *args):
        self.p.indent_tracking = self.prev_state
