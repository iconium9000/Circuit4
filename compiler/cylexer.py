# cylexer.py
import re
from dataclasses import dataclass

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
class lextok:
    str:str
    slen:int
    tidx:int
    lnum:int
    lidx:int

class strtok(lextok): pass
class idftok(lextok): pass
class numtok(lextok): pass
class opstok(lextok): pass
class tabtok(lextok): pass
class endtok(lextok): pass

class lexer:

    def __init__(self, filename:str, file:str):
        self.filename = filename
        file = '\n' + file + '\n\n\\'
        self.fidx_end = 0
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
        self.lnum = 0 # changes with iterator
        self.tidx = 0 # changes with iterator
        self.fidx_start = -1 # changes with iterator

        def gettoks():    
            while self.fidx_start < self.fidx_end:
                self.fidx_start = self.fidx_end
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
            self.error("lexer no move", self.lnum, self.lidx_start())
        self.toks = tuple(gettoks())
    
    def lidx(self, fidx:int):
        return fidx - self.ls_fidxs[self.lnum]
    
    def lidx_start(self):
        return self.fidx_start - self.ls_fidxs[self.lnum]

    def error(self, msg:str, lnum:int, lidx:int):
        print(f'File "{self.filename}", line {lnum}')
        print(self.lines[lnum])
        print(' ' * lidx + '^')
        print(msg)
        exit(-1)

    def next(self, t:type[lextok], pat:str, end:int):
        self.fidx_end = end
        while self.fidx_start > self.le_fidxs[self.lnum]:
            self.lnum += 1
        r = t(pat, len(pat), self.tidx, self.lnum, self.lidx(self.fidx_start))
        self.tidx += 1
        return r

    def tabpat(self):
        if m := nwlpat.match(self.file, self.fidx_end):
            if m2 := spcpat.match(self.file, m.end()):
                s,e = m2.span()
                pat = self.file[s:e]
                return self.next(tabtok, pat, e)
            return self.next(tabtok, str(), m.end())

    def spcpat(self):
        if m := spcpat.match(self.file, self.fidx_end):
            self.fidx_end = m.end()
            return True

    def opspat(self):
        if m := opspat.match(self.file, self.fidx_end):
            s,e = m.span()
            pat = self.file[s:e]
            return self.next(opstok, pat, e)

    def strpat(self) -> 'lextok | None':
        pat:str = str()
        if m := strpat.match(self.file, self.fidx_end):
            s, e = m.span()
            c = self.file[s:e]
            f,l = '\\' + c, len(c)
            while 0 <= (i := self.file.find(f, e)):
                pat += self.file[e:i] + c
                e = i+1+l
            if 0 <= (i := self.file.find("'''", e)):
                pat += self.file[e:i]
                if l == 1 and 0 <= pat.find('\n'):
                    self.error("unexpected newline in string", self.lnum, self.lidx_start())
                return self.next(strtok, pat, s, e+l)
            self.error("end string seq never found", self.lnum, self.lidx_start())

    def idfpat(self) -> 'lextok | None':
        if m := idfpat.match(self.file, self.fidx_end):
            s,e = m.span()
            pat = self.file[s:e]
            if pat in keywords:
                return self.next(opstok, pat, e)
            return self.next(idftok, pat, e)

    def numpat(self) -> 'lextok | None':
        if m := numpat.match(self.file, self.fidx_end):
            s,e = m.span()
            pat = self.file[s:e]
            return self.next(numtok, pat, e)

    def badpat(self) -> 'lextok | None':
        if self.fidx_end < self.filelen:
            pat = self.file[(s := self.fidx_end)]
            self.error(f"unexpected char '{pat}'", self.lnum, self.lidx_start())
