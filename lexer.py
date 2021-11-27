# lexer.py
import sys
import re
from typing import Callable, Generator

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

class BadChar(Exception): pass

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

class parsenode:
    
    def __init__(self, parser:'parser'):
        raise NotImplementedError(self.__class__.__name__)

class parsefail(Exception): pass

class parser:

    def __init__(self, file:str):
        self.toks = list(lexer(file))
        self.num_toks = len(self.toks)
        self.idx = 0

    def __next__(self):
        idx = self.idx
        if self.num_toks <= idx:
            raise StopIteration
        self.idx += 1        
        return self.toks[idx]

    def identifier(self):
        tok,val = next(self)
        if tok == 'idf': return val
        raise parsefail('identifier', tok, val)
     
    def tryops(self, *ops:str):
        tok,val = next(self)
        if tok == 'op' and val in ops: return val
        raise parsefail('mchop', ops, (tok,val))

    def tryor(self, *args:Callable[['parser'],parsenode]):
        idx = self.idx
        fails:list[parsefail] = []
        for arg in args:
            self.idx = idx
            try: return arg(self)
            except parsefail as e: fails.append(e)
        raise parsefail('tryor', *fails)

    def trywhile(self, arg:Callable[['parser'],parsenode], min:int=0):
        try:
            ret:list[parsenode] = []
            idx = -1
            while self.idx > idx:
                idx = self.idx
                ret.append(arg(self))
            raise parsefail('trywhile', 'nomove')
        except StopIteration:
            if len(ret) < min:
                raise parsefail('trywhile', 'min', len(ret), min)
            return ret

    def tryoptional(self, arg:Callable[['parser'],parsenode]):
        idx = self.idx
        try: return arg(self)
        except parsefail:
            self.idx = idx
            return None

class identifier(parsenode):
    def __init__(self, parser:parser):
        self.name = parser.identifier()

class translation_unit(parsenode):
    def __init__(self, parser:parser):
        self.args = parser.trywhile(external_declaration)

def external_declaration(parser:parser):
    return parser.tryor(function_definition, declaration)

class function_definition(parsenode):
    def __init__(self, parser:parser):
        self.specifiers = parser.trywhile(declaration_specifier)
        self.declarator = declarator(parser)
        self.declarations = parser.trywhile(declaration)
        self.compound_statement = compound_statement(parser)

def declaration_specifier(parser:parser):
    return parser.tryor(
        storage_class_specifier,
        type_specifier,
        type_qualifier
    )

class storage_class_specifier(parsenode):
    def __init__(self, parser:parser):
        self.specifier = parser.tryops('auto','register','static','extern','typedef')

def type_specifier(parser:parser):
    return parser.tryor(literal_type,
        struct_or_union_specifier,
        enum_specifier, typedef_name)

class literal_type(parsenode):
    def __init__(self, parser:parser):
        self.name = parser.tryops('void','char','short','int',
            'long','float','double','signed','unsigned')

class struct_or_union_specifier(parsenode):
    def __init__(self, parser:parser):
        self.struct_or_union = parser.tryops('struct','union')
        self.identifier = parser.tryoptional(identifier)
        try:
            idx = parser.idx
            parser.tryops('{')
            self.struct_declarations = parser.trywhile(struct_declaration, min=1)
            parser.tryops('}')
        except parsefail:
            if not self.identifier:
                raise parsefail('struct_or_union_specifier', 'neither')
            parser.idx = idx
            self.struct_declarations = None

class struct_declaration(parsenode): pass
class specifier_qualifier(parsenode): pass
class struct_declarator_list(parsenode): pass
class struct_declarator(parsenode): pass

class declarator(parsenode):
    def __init__(self, parser:'parser'):
        self.pointer = parser.tryoptional(pointer)
        self.direct_declarator = direct_declarator(parser)

class pointer(parsenode):
    def __init__(self, parser:parser):
        parser.tryops('*')
        self.type_qualifiers = parser.trywhile(type_qualifier)
        self.pointer = parser.tryoptional(pointer)

class type_qualifier(parsenode):
    def __init__(self, parser:parser):
        self.name = parser.tryops('const','volatile')

class direct_declarator(parsenode): pass
class constant_expression(parsenode): pass
class conditional_expression(parsenode): pass
class logical_or_expression(parsenode): pass
class logical_and_expression(parsenode): pass
class inclusive_or_expression(parsenode): pass
class exclusive_or_expression(parsenode): pass
class and_expression(parsenode): pass
class equality_expression(parsenode): pass
class relational_expression(parsenode): pass
class shift_expression(parsenode): pass
class additive_expression(parsenode): pass
class multiplicative_expression(parsenode): pass
class cast_expression(parsenode): pass
class unary_expression(parsenode): pass
class postfix_expression(parsenode): pass
class primary_expression(parsenode): pass
class constant(parsenode): pass
class expression(parsenode): pass
class assignment_expression(parsenode): pass
class assignment_operator(parsenode): pass
class unary_operator(parsenode): pass
class type_name(parsenode): pass
class parameter_type_list(parsenode): pass
class parameter_list(parsenode): pass
class parameter_declaration(parsenode): pass
class abstract_declarator(parsenode): pass
class direct_abstract_declarator(parsenode): pass

class enum_specifier(parsenode):
    def __init__(self, parser:parser):
        parser.tryops('enum')
        self.identifier = parser.tryoptional(identifier)
        try:
            idx = parser.idx
            parser.tryops('{')
            self.enumerator_list = enumerator_list(parser)
            parser.tryops('}')
        except parsefail:
            if not self.identifier:
                raise parsefail('enum_specifier', 'neigther')
            parser.idx = idx
            self.enumerator_list = None

class enumerator_list(parsenode): pass
class enumerator(parsenode): pass
class typedef_name(identifier): pass

class declaration(parsenode):
    def __init__(self, parser:parser):
        self.declaration_specifiers = parser.trywhile(declaration_specifier, min=1)
        self.init_declarator = parser.trywhile(init_declarator)
        parser.tryops(';')

class init_declarator(parsenode): pass
class initializer(parsenode): pass
class initializer_list(parsenode): pass
class compound_statement(parsenode): pass
class statement(parsenode): pass
class labeled_statement(parsenode): pass
class expression_statement(parsenode): pass
class selection_statement(parsenode): pass
class iteration_statement(parsenode): pass
class jump_statement(parsenode): pass

def main(filepath:str):
    with open(filepath, 'r') as f:
        file = f.read()
    tree = translation_unit(parser(file))

if __name__ == "__main__":

    main(*sys.argv[1:])
