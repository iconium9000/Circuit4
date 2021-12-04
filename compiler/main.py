# main.py
import sys
from cyparsefuns import *

def test():
    p = parser('test.py', 
        "a - b / c ** d // h is not -g"# - 'test' 'ing'"
        "% i != j == k > 17 > 3 and l or m or not not n")
    p.nexttok(tabtok)
    n = p.rule(disjunction_r)
    c = compile(n.itc)

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    p = parser(filename, file)
    r = file_r(p)

if __name__ == "__main__":
    filename = sys.argv[1]

    test()
    # main(filename)

