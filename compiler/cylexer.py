# cylexer.py

from dataclasses import dataclass
import re
from typing import Generator, Iterable, TypeVar

@dataclass
class trace:
    opname:str
    args:'tuple[trace, ...]|None'=None

    def __str__(self):
        if self.args:
            return self.opname + '(' + ','.join(str(arg) for arg in self.args) + ')'
        return self.opname

T = TypeVar('T')
def reverse(t:tuple[T, ...]): return (t[i] for i in range(len(t)-1, -1, -1))

class idmap:
    def __init__(self):
        self._map:dict[int,str] = {}
        self._idx = 0
    
    def idx(self, i:'instruction|register'):
        if idx := self._map.get(id(i)):
            return idx
        self._idx += 1
        idx = i.__class__.__name__[0] + str(self._idx)
        self._map[id(i)] = idx
        return idx

class register: pass

@dataclass
class instruction:
    next:'instruction'

@dataclass
class identifier_inst(instruction):
    target:register
    idf:str

@dataclass
class number_inst(instruction):
    target:register
    num:str

@dataclass
class string_inst(instruction):
    target:register
    string:str

@dataclass
class assign_inst(instruction):
    target:register
    arg:register

@dataclass
class await_inst(instruction):
    target:register
    arg:register

@dataclass
class binary_op_inst(instruction):
    op:str
    target:register
    arga:register
    argb:register

class compare_inst(binary_op_inst): pass

@dataclass
class unary_op_inst(instruction):
    op:str
    target:register
    arg:register

@dataclass
class branch_inst(instruction):
    '''
    go to next if reg is true;
    go to branch if reg is false
    '''

    branch:instruction
    test:register

@dataclass
class except_inst(instruction):
    raise_to:'register|None'
    exc_type:register
    exc_value:register
    exc_traceback:register

@dataclass
class exit_inst(instruction):
    code:register
    next:None

@dataclass
class control:
    raise_to:'instruction'
    break_to:'instruction|None'=None
    continue_to:'instruction|None'=None
    return_to:'instruction|None'=None
    yield_to:'instruction|None'=None
    yields:bool=False

class tree_node:
    def trc(self) -> trace:
        raise NotImplementedError(f'trc not implemented for {self.__class__.__name__}')

    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        raise NotImplementedError(f'itc not implemented for {self.__class__.__name__}')

    def __str__(self):
        return str(self.trc())

nwlpat = re.compile(r'(\#[^\n]*| |\n)*\n')
spcpat = re.compile(r' +')
idfpat = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
numpat = re.compile(r'0(x|X)[0-9a-fA-F]+|0(b|B)[01]+|0[0-7]*|[0-9]+')
badpat = re.compile(r'.')
strpat = re.compile(r"\"|\'|\'\'\'")

opsset = [
    '!', '?', '|', '&', '/', '{', '=', '<<=',
    '<', '-', '@=', '^', '}', ':=', '&=', '%',
    '[', '**', '>>', '>>=', '|=', ':', '==',
    '@', '*=', '<>', '->', '%=', '**=', '~',
    '//=', '!=', '.', '>', '-=', ';', ',',
    '//', ']', '*', '/=', '...', ')', '(',
    '^=', '<<', '<=', '>=', '+=', '+']
opsset.sort(key=lambda s : len(s)); opsset.reverse()
opspat = re.compile('|'.join('\\' + '\\'.join(op) for op in opsset))

keywords = {'raise', 'continue', 'as', 'in', 'is', 'else',
    'or', 'def', 'finally', 'del', 'None', 'for',
    'class', 'False', 'while', 'lambda', 'pass',
    'True', 'None', 'for', 'class', 'return', 'and',
    'nonlocal', 'with', 'async', 'global', 'elif', 'break',
    'with', 'async', 'global', 'False', 'while', 'lambda',
    'pass', 'True', 'return', 'and', 'nonlocal', 'with',
    'async', 'global', 'elif', 'break', 'await', 'not',
    'import', 'await', 'not', 'import', 'assert', 'if', 'from'}

@dataclass
class lextok(tree_node):
    str:str
    slen:int
    tidx:int
    lnum:int
    lidx:int

class numtok(lextok):
    def trc(self) -> trace:
        return trace(f'num:"{self.str}"')
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return number_inst(next, reg, self.str)

class strtok(lextok):
    def trc(self) -> trace:
        return trace(f'str:"{self.str}"')
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return string_inst(next, reg, self.str)

class idftok(lextok):
    def trc(self) -> trace:
        return trace(f'idf:"{self.str}"')
    def itc(self, ctrl:control, next:instruction, reg:register) -> instruction:
        return identifier_inst(next, reg, self.str)

class tabtok(lextok): pass
class opstok(lextok): pass
class badtok(lextok): pass
class endtok(lextok): pass

class lexer(Iterable[lextok]):

    def __init__(self, file:str):
        file = '\n' + file + '\n\n\\'
        self.endidx = 0
        self.file = str()
        self.lines:'list[str]' = []

        fidx = 0
        self.ls_fidxs:'list[int]' = []
        self.le_fidxs:'list[int]' = []
        for line in file.split('\n'):
            self.ls_fidxs.append(fidx)
            if line and line[-1] == '\\':
                line = line[:-1]
                fidx += len(line)
                tfidx = fidx
                self.file += line
            else:
                tfidx = fidx + len(line)
                self.file += line + '\n'
                fidx = tfidx+1
            self.le_fidxs.append(tfidx)
            self.lines.append(line)

        self.filelen = len(self.file)
        self.lidx = 0 # changes with iterator
        self.tidx = 0 # changes with iterator
        self.startidx = -1 # changes with iterator
    
    def next(self, t:type[lextok], pat:str, end:int):
        self.endidx = end
        while self.startidx > self.le_fidxs[self.lidx]:
            self.lidx += 1
        ls_fidx = self.ls_fidxs[self.lidx]
        r = t(pat, len(pat), self.tidx, self.lidx, self.startidx - ls_fidx)
        self.tidx += 1
        return r

    def tabpat(self):
        if m := nwlpat.match(self.file, self.endidx):
            if m2 := spcpat.match(self.file, m.end()):
                s,e = m2.span()
                pat = self.file[s:e]
                return self.next(tabtok, pat, e)
            return self.next(tabtok, str(), m.end())

    def spcpat(self):
        if m := spcpat.match(self.file, self.endidx):
            self.endidx = m.end()
            return True

    def opspat(self):
        if m := opspat.match(self.file, self.endidx):
            s,e = m.span()
            pat = self.file[s:e]
            return self.next(opstok, pat, e)

    def strpat(self):
        if m := strpat.match(self.file, self.endidx):
            s, e = m.span()
            c = self.file[s:e]
            f,l,pat = '\\' + c, len(c), str()
            while 0 <= (i := self.file.find(f, e)):
                pat += self.file[e:i] + c
                e = i+1+l
            if 0 <= (i := self.file.find("'''", e)):
                pat += self.file[e:i]
                if l == 1 and 0 <= pat.find('\n'):
                    return self.next(badtok, "unexpected newline in string", e+l)
                return self.next(strtok, pat, s, e+l)
            return self.next(badtok, f'end string seq never found', len(self.file))

    def idfpat(self):
        if m := idfpat.match(self.file, self.endidx):
            s,e = m.span()
            pat = self.file[s:e]
            if pat in keywords:
                return self.next(opstok, pat, e)
            return self.next(idftok, pat, e)

    def numpat(self):
        if m := numpat.match(self.file, self.endidx):
            s,e = m.span()
            pat = self.file[s:e]
            return self.next(numtok, pat, e)

    def badpat(self):
        if self.endidx < self.filelen:
            pat = self.file[(s := self.endidx)]
            return self.next(badtok, f'unexpected char "{pat}"', s, s+1)

    def __iter__(self):
        while self.startidx < self.endidx:
            self.startidx = self.endidx
            if info := self.strpat(): yield info
            elif info := self.tabpat(): yield info
            elif info := self.spcpat(): pass
            elif info := self.idfpat(): yield info
            elif info := self.opspat(): yield info
            elif info := self.numpat(): yield info
            elif info := self.badpat(): yield info
            else:
                yield self.next(endtok, "EOF", self.filelen)
                return
        yield self.next(badtok, "no-move", self.filelen)
