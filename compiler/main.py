# main.py
import sys
import cyparser
import cyparsefuns as funs
import cycompiler as comp
import cyassembler as assy

class parser_manip:

    def __init__(self, filename:str, file:str):
        p = cyparser.parser(filename, file)
        n = funs.file_r(p)


        ctx = comp.context('program', 'start')
        paths = n.asm(ctx)
        xctx = comp.context('exit', 'pass')
        for pctx in paths._ctxs.values():
            pctx._setctxs(n=xctx)

        assy.assember(ctx)
        print('main success')

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    parser_manip(filename, file)

if __name__ == "__main__":
    filename = sys.argv[1]

    # test()
    main(filename)
