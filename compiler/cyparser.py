# cyparser.py
from typing import Callable, Literal, NoReturn
import cylexer as lex
from cytree import tree_node, tree_range

class parser:

    def __init__(self, filename:str, file:str):
        self.lexer = lex.lexer(filename, file)
        self.tmap:'dict[tuple[int,int],tree_range|Literal[True]]' = {}
        self.indent = 0
        self.indent_tracking = True
        self.tok = self.lexer.toks[0]

    def error(self, msg:str) -> NoReturn:
        self.lexer.error(msg, self.tok.lnum, self.tok.lidx)

    def newline(self):
        return # TODO

    def indent(self):
        return # TODO
    
    def dedent(self):
        return # TODO

    def ignore_tracking(self, start:str, rule:'Callable[[parser],tree_node|None]', end:str):
        tok = self.tok
        tracking = self.indent_tracking
        self.indent_tracking = False
        if r := self.nextop({start}) and rule(self):
            self.indent_tracking = tracking
            if self.nextop({end}): return r
        else: self.indent_tracking = tracking
        self.tok = tok

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

    def rule_err(self, rule:'Callable[[parser],tree_node|None]', err:str) -> 'tree_range | NoReturn':
        return self.rule(rule) or self.error(err)

    def next(self):
        tok = self.tok
        self.tok = self.lexer.toks[self.tok.tidx+1]
        if not self.indent_tracking:
            self.nexttok(lex.tabtok)
        return tok

    def gettok(self, lex:type[lex.lextok], err:'str|None'=None):
        if isinstance(self.tok, lex):
            return self.tok
        if err: self.error(err)

    def nexttok(self, lex:type[lex.lextok], err:'str|None'=None):
        if isinstance(self.tok, lex):
            return self.next()
        if err: self.error(err)

    def getop(self, ops:set[str], err:'str|None'=None):
        if isinstance(tok := self.tok, lex.opstok) and tok.str in ops:
            return tok
        if err: self.error(err)

    def nextop(self, ops:set[str], err:'str|None'=None):
        if isinstance(tok := self.tok, lex.opstok) and tok.str in ops:
            self.next()
            return tok
        if err: self.error(err)

def todo(r:'Callable[[parser],tree_node|None]'):
    def _r(p:parser):
        p.error(f'"{r.__name__}" is Not Implemented')
    _r.__name__ = r.__name__
    return _r
