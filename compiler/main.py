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
        self.n = self.p.rule_err(funs.file_r, "failed to read file")

        exit_reg = comp.register('exit')
        exc_type = comp.register('exc-type')
        exc_value = comp.register('exc-value')
        exc_traceback = comp.register('exc-traceback')
        exc_info = exc_type, exc_value, exc_traceback
        stmts_reg = comp.register('file-stmts')

        exit_to = comp.exit_i(None, exit_reg)
        exit_fail = comp.number_i(exit_to, exit_reg, '1')
        exit_success = comp.number_i(exit_to, exit_reg, '0')
        raise_to = comp.except_i(exit_fail, None, None, exc_info)
        ctrl = comp.control(self, 0, 0, raise_to, exc_info)
        inst = self.n.itc(ctrl, exit_success, stmts_reg)

        comp.compiler(inst)

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
