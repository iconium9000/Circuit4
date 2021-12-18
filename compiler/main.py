# main.py
import sys
from typing import Iterable, NoReturn
import cyparser
import cyparsefuns as funs
import cycompiler as comp

class parser_manip:

    def __init__(self, filename:str, file:str):
        p = cyparser.parser(filename, file)
        n = funs.file_r(p)


        ctx = comp.context('program', 'start')
        n.asm(ctx)

        print('main success')

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    parser_manip(filename, file)

if __name__ == "__main__":
    filename = sys.argv[1]

    # test()
    main(filename)
