
# cythonlexer.py
from dataclasses import dataclass
import re

nwlpat = re.compile(r'(\#[^\n]*| |\n)*\n')
tabpat = re.compile(r' *')
spcpat = re.compile(r' +')
idfpat = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
numpat = re.compile(r'0(x|X)[0-9a-fA-F]+|0(b|B)[01]+|0[0-7]*|[0-9]+')
strpat = re.compile(r'\"(\\\"|[^\"])*\"|\'(\\\'|[^\'])*\'')
badpat = re.compile(r'.')

opslist = (
    '| & / { = <<= < - @= ^ } := &= '
    '% [ ** >> >>= |= : == @ *= <> -> '
    '%= **= ~ //= != . > -= ; , // ] '
    '* /= ... ) ( ^= << <= >= += +'.split())
opslist.sort(key=lambda s : len(s))
opslist.reverse()
opslist = ['\\' + '\\'.join(op) for op in opslist]
opspat = re.compile('|'.join(opslist))

keywords = set(
    'def del pass break continue return raise from import '
    'as global nonlocal assert if while lambda class '
    'for in else elif finally with or and not None True False'.split())

@dataclass
class matchinfo:
    string:str
    filename:str
    lidx:int
    start:int
    end:int
    line:str
@dataclass
class lextok: info:matchinfo

@dataclass
class optok(lextok): op:str

@dataclass
class idftok(lextok): name:str

@dataclass
class tabtok(lextok): tabs:int

@dataclass
class numtok(lextok): num:str

@dataclass
class strtok(lextok): string:str

@dataclass
class badtok(lextok): pass

class lexer:

    def __init__(self, filename:str):
        with open(filename, 'r') as f:
            file = f.read()
        self.filename = filename
        file = '\n' + file + '\n\n\\'
        self.fidx = 0
        self.file = str()
        self.lines:'list[str]' = []
        self.lidx = 0

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

    def match(self, pattern:re.Pattern[str]):
        m = pattern.match(self.file, self.fidx)
        if not m: return None
        start,end = m.span()
        self.fidx = end
        while start > self.le_fidxs[self.lidx]:
            self.lidx += 1
        ls_fidx = self.ls_fidxs[self.lidx]
        string = self.file[start:end]
        start -= ls_fidx
        end -= ls_fidx
        line = self.lines[self.lidx]
        return matchinfo(string,self.filename,self.lidx,start,end,line)

    def __new__(cls, filename:str):
        chars = super().__new__(cls)
        cls.__init__(chars, filename)
        idx = -1
        while chars.fidx > idx:
            idx = chars.fidx
            if m := chars.match(strpat):
                yield strtok(m, m.string)
            elif chars.match(nwlpat):
                info = chars.match(tabpat)
                yield tabtok(info, len(info.string))
            elif chars.match(spcpat): pass
            elif m := chars.match(idfpat):
                tok = optok if m.string in keywords else idftok
                yield tok(info, m.string)
            elif m := chars.match(numpat): yield numtok(m, m.string)
            elif m := chars.match(opspat): yield optok(m, m.string)
            elif m := chars.match(badpat): yield badtok(m)
            else: return
        raise Exception('nomove')
