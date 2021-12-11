# main.py
import sys
from typing import Iterable, NoReturn
import cyparser
import cyparsefuns as funs
import cycompiler as comp
from cycompiler import register

class parser_manip(comp.context_tracing):

    def __init__(self, filename:str, file:str):
        self.p = cyparser.parser(filename, file)
        self.n = self.p.rule_err(funs.file_r, "failed to read file")
        self.sidx, self.eidx = 0, 0

        print('success')

    def update(self, startidx: int, stopidx: int) -> tuple[int, int]:
        r = self.sidx, self.eidx
        self.sidx, self.eidx = startidx, stopidx
        return r

    def error(self, msg: str) -> NoReturn:
        tok = self.p.lexer.toks[self.sidx]
        self.p.lexer.error(msg, tok.lnum, tok.lidx)

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
