# lexer.py
import sys
from cythonparser import parser
from lexfuns import file

def main(filepath:str):
    p = parser(filepath)
    n = file(p)
    print(n)

if __name__ == "__main__":
    main(*sys.argv[1:])
