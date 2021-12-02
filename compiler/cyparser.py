# cyparser.py
from typing import Callable, Literal
from cylexer import *

class parser_node: pass

@dataclass
class parser_range:
    node:'parser_node|lextok'
    start:lextok
    end:lextok

class parser:

    def __init__(self, filename:str, file:str):
        self.filename = filename
        self.lexer = lexer(file)
        self.toks = list(self.lexer)
        self.ntoks = len(self.toks)
        self.tmap:'dict[tuple[int,int],parser_range|Literal[True]]' = {}
        self.indent = 0
        self.indent_tracking = True
        self.tok = self.toks[0]
    
    def rule(self, rule:'Callable[[parser],lextok|parser_node|parser_range|None]'):
        tup = self.tok.idx, id(rule)
        if ret := self.tmap.get(tup):
            if ret is True: return
            self.tok = ret.end
            return ret
        self.tmap[tup] = True
        tok = self.tok
        if ret := rule(self):
            if not isinstance(ret, parser_range):
                ret = parser_range(ret, tok, self.tok)
            self.tmap[tup] = ret
            return ret
        self.tok = tok

    def rules(self, *rules:'Callable[[parser],lextok|parser_node|parser_range|None]'):
        for rule in rules:
            if r := self.rule(rule):
                return r

    def next(self):
        self.tok = self.toks[self.tok.tidx+1]
        if self.indent_tracking: return
        self.nexttok(tabtok)

    def gettok(self, *lexs:type[lextok], ops:'set[str]|None'=None, err:'str|None'=None):
        rlex = None
        for lex in lexs:
            if isinstance(self.tok, lex):
                rlex = lex; break
        if rlex and (not ops or self.tok.string in ops):
            return self.tok
        elif err: syntax_error(err)(self)

    def nexttok(self, *lexs:type[lextok], ops:'set[str]|None'=None, syntax:'str|None'=None):
        if tok := self.gettok(*lexs, ops, syntax):
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

def syntax_error(msg:str):
    def _syntax_error(p:parser):
        print(f'File "{p.filename}", line {p.tok.lnum}')
        print(p.lexer.lines[p.tok.lnum])
        print(' ' * p.tok.lidx + '^')
        print(msg)
        exit(-1)
    return _syntax_error
