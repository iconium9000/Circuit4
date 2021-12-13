# main.py
import sys
from typing import Iterable, NoReturn
import cyparser
import cyparsefuns as funs
import cycompiler as comp
from cycompiler import context, register, instruction

class parser_manip(comp.context_tracing):

    def error(self, msg: str) -> NoReturn:
        tok = self.p.lexer.toks[self.sidx]
        self.p.lexer.error(msg, tok.lnum, tok.lidx)

    def update(self, startidx: int, stopidx: int) -> tuple[int, int]:
        r = self.sidx, self.eidx
        self.sidx, self.eidx = startidx, stopidx
        return r

    def assign_context(self, i: instruction):
        self.insts[id(i)] = self.sidx, self.eidx

    def __init__(self, filename:str, file:str):
        self.p = cyparser.parser(filename, file)
        self.n = self.p.rule_err(funs.file_r, "failed to read file")
        self.insts:dict[int,tuple[int,int]] = {}
        self.sidx, self.eidx = 0, 0

        ctx = context(self)
        exit_code = register('prog-exit')
        nxt = comp.exit_i(exit_code)
        nxt = comp.bool_lit_i(ctx, nxt, exit_code, True)
        i = self.n.asm(ctx, nxt, register('prog-block'))

        comp.compiler(i)

def test():
    parser_manip('test.py',
        "a - b / c ** d // h is not (-g,)"# - 'test' 'ing'"
        "% i != j == k > 17 > 3 and l or not not n")

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    parser_manip(filename, file)

if __name__ == "__main__":
    filename = sys.argv[1]

    # test()
    main(filename)
