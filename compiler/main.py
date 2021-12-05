# main.py
import sys
from typing import Iterable, NoReturn
import cylexer as lex
import cyparser
import cyparsefuns as funs
import cycompiler as comp

class parser_manip(comp.control_manip):

    def __init__(self, filename:str, file:str):
        self.p = cyparser.parser(filename, file)
        self.p.nexttok(lex.tabtok)

        self.n = self.p.rule_err(funs.disjunction_r, "failed to read file")
        c = comp.compile(self)
        print(c)
    
    def itc(self, c: comp.control, i: comp.instruction, r: comp.register) -> comp.instruction:
        return self.n.itc(c, i, r)

    def error(self, msg: str, lnum: int, lidx: int) -> NoReturn:
        self.p.lexer.error(msg, lnum, lidx)

    def getlines(self, slnum: int, slidx: int, elnum: int, elidx) -> Iterable[str]:
        lines = self.p.lexer.lines
        if slnum == elnum:
            yield lines[slnum][slidx:elidx]
            return
        yield lines[slnum][slidx:]
        for lnum in range(slnum+1, elnum-1, 1):
            yield lines[lnum]
        yield lines[elnum][:elidx]

def test():
    parser_manip('test.py', 
        "a - b / c ** d // h is not -g"# - 'test' 'ing'"
        "% i != j == k > 17 > 3 and l or m or not not n")
    # p = cyparser.parser('test.py', 'a or b and c')

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    p = cyparser.parser(filename, file)
    r = funs.file_r(p)

if __name__ == "__main__":
    filename = sys.argv[1]

    test()
    # main(filename)

