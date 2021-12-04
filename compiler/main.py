# main.py
import sys
import cylexer
import cyparser
import cyparsefuns
def test():
    p = cyparser.parser('test.py', 
        "a - b / c ** d // h is not -g"# - 'test' 'ing'"
        "% i != j == k > 17 > 3 and l or m or not not n")
    p.nexttok(cylexer.tabtok)
    n = p.rule(cyparsefuns.disjunction_r)
    c = compile(n.itc)

def main(filename:str):
    with open(filename, 'r') as f:
        file = f.read()
    p = cyparser.parser(filename, file)
    r = cyparsefuns.file_r(p)

if __name__ == "__main__":
    filename = sys.argv[1]

    test()
    # main(filename)

