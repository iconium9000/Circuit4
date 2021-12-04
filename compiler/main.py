# main.py
import sys
import cyparsefuns

if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        file = f.read()
    p = cyparsefuns.parser(filename, file)
    # r = cyparsefuns.file_r(p)
