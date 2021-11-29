# cythonparser.py

from typing import Callable
from cythonlexer import lexer

class tabs:
    def __init__(self, p:'parser', f:Callable):
        self.p = p
        self.name = f.__name__
    def __enter__(self):
        print(self.p.tabs(), self.name, 'tabs')
        self.tabnum = self.p.tabnum
        self.p.tabnum += 1
    def __exit__(self, *args): self.p.tabnum = self.tabnum

def withtabs(f:'Callable[[parser],parsenode]'):
    def _withtabs(p:'parser'):
        with tabs(p, f): return f(p)
    _withtabs.__name__ = f.__name__
    return _withtabs

class parsenode:
    def __init__(self, p:'parser'):
        raise p.parsererror(self.__class__.__name__, NotImplemented)

class parsererror(Exception): pass

class ignoreindent:
    def __init__(self, p:'parser'):
        self.p = p
    def __enter__(self):
        self.tracking = self.p.tracking
        self.p.tracking = False
    def __exit__(self, *args):
        self.p.tracking = self.tracking

class trackindent:
    def __init__(self, p:'parser'):
        self.p = p
    def __enter__(self):
        self.tracking = self.p.tracking
        self.p.tracking = True
    def __exit__(self, *args):
        self.p.tracking = self.tracking

class parser:
    def __init__(self, filepath:str):
        self.lexlist = list(lexer(filepath))
        self.tabnum = 0
        self.lexlist_len =  len(self.lexlist)
        self.lexidx = 0
        self.tracking = False

        with open('lexer.log', 'w') as f:
            print(*self.lexlist, file=f, sep='\n')
    
    def tabs(self): return '  ' * self.tabnum + ' '

    def parsererror(self, *args:str):
        return parsererror(*args)

    def trynewline(self):
        raise NotImplementedError('trynewline')

    def tryindent(self):
        raise NotImplementedError('tryindent')

    def trydedent(self):
        raise NotImplementedError('trydedent')

    def tryendmarker(self):
        raise NotImplementedError('tryendmarker')

    def tryidentifier(self):
        raise NotImplementedError('tryidentifier')

    def trystrings(self):
        raise NotImplementedError('trystrings')

    def tryinteger(self):
        raise NotImplementedError('trywhile')

    def tryops(self, *ops:str, optional:bool=False):
        raise NotImplementedError('tryops')

    def trywhile(self, arg:Callable[['parser'],parsenode], min=0):
        raise NotImplementedError('trywhile')

    def tryor(self, *args:Callable[['parser'],parsenode], optional:bool=False):
        raise NotImplementedError('tryor')

    def tryoptional(self, arg:Callable[['parser'],parsenode]):
        raise NotImplementedError('tryoptional')
