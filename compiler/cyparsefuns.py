# cyparsefuns.py
from cyparser import *

def file_r(p:parser):
    with indent_tracking(p, True):
        if tok := p.nexttok(tabtok):
            p.indent = tok.slen
            r = p.rule(statements_r)
            p.nexttok(endtok, err="failed to reach end of file")
            return r

def statements_r(p:parser):
    def getargs():
        while r := p.rule(statement_r): yield r
    return block_n(*getargs())

def statement_r(p:parser):
    if p.gettok(tabtok): return
    return p.rules(compound_stmt_r, simple_stmts_r)

def compound_stmt_r(p:parser):
    if op := p.gettok(opstok, ops=compound_stmt_map.keys()):
        p.rules(*compound_stmt_map[op.str])

def simple_stmts_r(p:parser): p.syntax_error('simple_stmts_r is NotImplemented')

def function_def_r(p:parser): p.syntax_error('function_def_r is NotImplemented')
def if_stmt_r(p:parser): p.syntax_error('if_stmt_r is NotImplemented')
def class_def_r(p:parser): p.syntax_error('class_def_r is NotImplemented')
def with_stmt_r(p:parser): p.syntax_error('with_stmt_r is NotImplemented')
def for_stmt_r(p:parser): p.syntax_error('for_stmt_r is NotImplemented')
def try_stmt_r(p:parser): p.syntax_error('try_stmt_r is NotImplemented')
def while_stmt_r(p:parser): p.syntax_error('while_stmt_r is NotImplemented')
def match_stmt_r(p:parser): p.syntax_error('match_stmt_r is NotImplemented')

def decorator_stmt_r(p:parser): p.syntax_error('decorator_stmt_r is NotImplemented')
def async_stmt_r(p:parser): p.syntax_error('async_stmt_r is NotImplemented')

compound_stmt_map = {
    '@': decorator_stmt_r,
    'def': function_def_r,
    'if': if_stmt_r,
    'class': class_def_r,
    'async': async_stmt_r,
    'with': with_stmt_r,
    'for': for_stmt_r,
    'try': try_stmt_r,
    'while': while_stmt_r,
    'match': match_stmt_r,
}