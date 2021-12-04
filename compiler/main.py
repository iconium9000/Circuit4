# main.py
import sys
from cyparsefuns import *

def compile(n:tree_node):
    exc_value = register()
    exc_type = register()
    exc_traceback = register()

    exit_to = exit_inst(None, exc_value)
    raise_to = except_inst(exit_to, None, exc_type, exc_value, exc_traceback)
    ctrl = control(raise_to)
    inst = n.itc(ctrl, exit_to, exc_value)

    return inst

def test():
    p = parser('test.py', 
        "a - b / c ** d // h is not -g"
        "% i != j == k > 17 > 3 and l or m or not not n")
    p.nexttok(tabtok)
    n = p.rule(disjunction_r)
    i = compile(n)

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    p = parser(filename, file)
    r = file_r(p)

if __name__ == "__main__":
    filename = sys.argv[1]

    test()
    # main(filename)

