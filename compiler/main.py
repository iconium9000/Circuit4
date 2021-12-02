# main.py
import sys
from cyparser import *

if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        file = f.read()
    p = parser(filename, file)
    syntax_error("Loaded successfully")(p)
