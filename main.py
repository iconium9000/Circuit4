# lexer.py
import sys
from cythonparser import parser, parsererror
from lexfuns import file_input

def main(filepath:str):
    p = parser(filepath)
    try:
        file_input(p)
    except parsererror as e:
        print('parsererror', e)
    except NotImplementedError as e:
        print('NotImplementedError', e)
    except AssertionError as e:
        print('AssertionError', e)

if __name__ == "__main__":
    main(*sys.argv[1:])
