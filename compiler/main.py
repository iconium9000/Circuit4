# main.py
import sys
import cylexer as lex
import cyparser
import cyparsefuns as funs
import cycompiler as comp

def test():
    p = cyparser.parser('test.py', 
        "a - b / c ** d // h is not -g"# - 'test' 'ing'"
        "% i != j == k > 17 > 3 and l or m or not not n")
    # p = cyparser.parser('test.py', 'a or b and c')
    n = p.rule(funs.file_r)
    c = comp.compile(n.itc)
    print(c)

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    p = cyparser.parser(filename, file)
    r = funs.file_r(p)

if __name__ == "__main__":
    filename = sys.argv[1]

    test()
    # main(filename)

