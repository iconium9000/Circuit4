import re
from typing import Generator

class charlist:

    def __init__(self, file:str):
        self.idx = 0
        self.file = file
        self.file_len = len(file)

    def match(self, pattern:re.Pattern[str]):
        m = re.match(pattern, self.file[self.idx:])
        if not m: return None
        start,end = m.span()
        start += self.idx
        self.idx += end
        return self.file[start:self.idx]

    def next(self):
        if self.idx >= self.file_len:
            raise StopIteration
        return self.file[self.idx]
    
    def move(self):
        self.idx += 1

strpat = re.compile(r'\"(\\\"|[^\"])*\"')
chrpat = re.compile(r'\'(\\\'|[^\'])*\'')
numpat = re.compile(r'0(x|X)[0-9a-fA-F]+|0(b|B)[01]+|0[0-7]*|[0-9]+')
idfpat = re.compile(r'[_a-zA-Z][_a-zA-Z0-9]*')
spcpat = re.compile(r'(\/\/[^\n]*\n|\/\*[^\*\/]*\*\/| |\t|\n)*')
opspat = re.compile(r'volatile|unsigned|register|continue|typedef|default|'
    r'switch|struct|static|sizeof|signed|return|extern|double|'
    r'while|union|short|float|const|break|void|long|goto|enum|else|char|case|auto|'
    r'int|for|if|do|'
    r'\>\>\=|\<\<\=|\.\.\.|'
    r'\|\||\|\=|\^\=|\>\>|\>\=|\=\=|\<\=|\<\<|'
    r'\/\=|\-\>|\-\=|\-\-|\+\=|\+\+|\*\=|\&\=|\&\&|\%\=|\!\=|'
    r'\~|\}|\||\{|\^|\]|\[|\?|\>|\=|\<|\;|\:|\/|\.|\-|\,|\+|\*|\)|\(|\&|\%|\!')

def lexer(file:str) -> 'Generator[tuple[str,str],None,None]':
    try:
        chars = charlist('\n' + file.replace('\\\n','') + '\n')
        while True:
            if m := chars.match(strpat): yield ('str', m)
            elif m := chars.match(chrpat): yield ('chr', m)
            elif chars.match(spcpat): pass
            elif m := chars.match(opspat): yield ('op', m)
            elif m := chars.match(numpat): yield ('num', m)
            elif m := chars.match(idfpat): yield ('idf', m)
            else: raise KeyError(chars.next())
    except StopIteration:
        return
