
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
    '! ? | & / { = <<= < - @= ^ } := &= '
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

    def __str__(self):
        return f'{self.lidx}:{self.start}:{self.end}'

@dataclass
class lextok:
    info:matchinfo

@dataclass
class optok(lextok):
    op:str
    def __str__(self):
        return str(('op', self.op, str(self.info)))

@dataclass
class idftok(lextok):
    name:str
    def __str__(self):
        return str(('name', self.name, str(self.info)))

@dataclass
class tabtok(lextok):
    tabs:int
    def __str__(self):
        return str(('tabs', self.tabs, str(self.info)))

@dataclass
class numtok(lextok):
    num:str
    def __str__(self):
        return str(('num', self.num, str(self.info)))

@dataclass
class strtok(lextok):
    string:str
    def __str__(self):
        return str(('str', self.string, str(self.info)))

@dataclass
class endtok(lextok):
    def __str__(self):
        return str(('end', str(self.info)))

@dataclass
class badtok(lextok):
    def __str__(self):
        return str(('bad', str(self.info)))

class charlist:

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

def lexer(filename:str):
    chars = charlist(filename)
    idx = -1
    while chars.fidx > idx:
        idx = chars.fidx
        if info := chars.match(strpat):
            yield strtok(info, info.string)
        elif chars.match(nwlpat):
            info = chars.match(tabpat)
            yield tabtok(info, len(info.string))
        elif chars.match(spcpat): pass
        elif info := chars.match(idfpat):
            tok = optok if info.string in keywords else idftok
            yield tok(info, info.string)
        elif info := chars.match(numpat): yield numtok(info, info.string)
        elif info := chars.match(opspat): yield optok(info, info.string)
        elif info := chars.match(badpat): yield badtok(info)
        else:
            yield endtok(matchinfo('',filename,chars.lidx,0,0,''))
            return

    raise Exception('nomove')
