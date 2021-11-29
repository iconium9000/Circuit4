from cythonlexer import optok
from cythonparser import parser, trackindent, ignoreindent, withtabs, parsenode, tabs, parsererror
from typing import Callable, Generator

@withtabs
class file_input(parsenode):
    def __init__(self, p:parser):
        with trackindent(p):
            p.trynewline()
            self.stmts = p.trywhile(stmt)
            p.tryendmarker()
