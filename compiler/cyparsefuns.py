# cyparsefuns.py
from cyparser import *

def todo(r:'Callable[[parser],tree_node|None]'):
    def _r(p:parser) -> 'tree_node|None':
        p.syntax_error(f'"{r.__name__}" is Not Implemented')
    _r.__name__ = r.__name__
    return _r

def file_r(p:parser):
    with indent_tracking(p, True):
        if tok := p.nexttok(tabtok):
            p.indent = tok.slen
            r = p.rule(statements_r)
            p.nexttok(endtok, err="failed to reach end of file")
            return r

def statements_r(p:parser):
    def getstmts():
        while r := p.rule(statement_r):
            if isinstance(r, statements_n):
                yield from r.args
            else: yield r
    if args := list(getstmts()):
        if len(args) == 1: return args[0]
        return statements_n(args)

def statement_r(p:parser):
    if p.gettok(tabtok): return
    return p.rules(compound_stmt_r, simple_stmts_r)

def compound_stmt_r(p:parser):
    if op := p.nextop(*compound_stmt_map.keys()):
        return p.rules(compound_stmt_map[op], err=f'"{op}" invalid syntax')

@todo
def simple_stmts_r(p:parser): pass

@todo
def function_def_r(p:parser): pass

def if_stmt_r(p:parser):

    def getblocks():
        if_case = p.rules(named_expression_r, err="missing 'if case'")
        p.nextop(':', err="missing ':'")
        if_block = p.rules(block_r, err="missing if block")
        yield if_case, if_block

        while p.nextop('elif'):
            elif_case = p.rules(named_expression_r, err="missing 'elif case'")
            p.nextop(':', err="missing ':")
            elif_block = p.rules(block_r, err="missing elif block")
            yield elif_case, elif_block
        
        if p.nextop('else'):
            p.nextop(':', err="missing ':")
            else_block = p.rules(block_r, err="missing else block")
            yield else_block

    return if_block_n((*getblocks(),))

@todo
def class_def_r(p:parser): pass
@todo
def with_stmt_r(p:parser): pass
@todo
def for_stmt_r(p:parser): pass
@todo
def try_stmt_r(p:parser): pass
@todo
def while_stmt_r(p:parser): pass
@todo
def match_stmt_r(p:parser): pass

@todo
def decorator_stmt_r(p:parser): pass
@todo
def async_stmt_r(p:parser): pass

compound_stmt_map = {
    '@': decorator_stmt_r,
    'def': function_def_r,
    'if': if_stmt_r,
    'class': class_def_r,
    'async': async_stmt_r,
    'with': with_stmt_r,
    'for': for_stmt_r,
    'try': try_stmt_r,
    'while': while_stmt_r,
    'match': match_stmt_r,
}

def assignment_expression(p:parser):
    if (name_tok := p.nexttok(idftok)) and p.nextop(':='):
        expr = p.rules(expression_r, err='no expression found in named expression')
        return assignment_n(name_tok, expr)

def named_expression_r(p:parser):
    return p.rules(assignment_expression, expression_r)

@todo
def block_r(p:parser): pass

def expression_r(p:parser):
    if p.nextop('lambda'):
        return p.rules(lambdadef_r, sys="missing lambda body")
    elif a := p.rule(disjunction):
        if p.nextop('if'):
            b = p.rules(disjunction_r, sys="missing if body")
            p.nextop('else', sys="missing 'else' token")
            c = p.rules(expression_r, sys="missing else body")
            return if_block_n(((a,b), c))
        return a

@todo
def lambdadef_r(p:parser): pass

binary,unary = True,False
disjunction_list:'tuple[tuple[bool,tuple[str|tuple[str,str]|tuple[str], ...]]]' = (
    (unary, 0, ('await',)), # await_primary
    (binary, -1, ('**',)), # power
    (unary, -1, ('~', '-', '+')), # factor
    (binary, 1, ('*', '/', '//', '%', '@')), # term
    (binary, 1, ('+', '-',)), # sum
    (binary, 1, ('>>', '<<')), # shift_expr
    (binary, 1, ('&',)), # bitwise_and
    (binary, 1, ('^',)), # bitwise_xor
    (binary, 1, ('|',)), # bitwise_or
    (binary, 0, (('is',), ('is','not'), 'in', ('not','in'),
        '>', '>=', '<', '<=', '!=', '==')), # comparison
    (unary, -1, (('not',),)), # inversion
    (binary, 1, ('and',)), # conjunction
    (binary, 1, ('or',)), # disjunciton
)
binary_ops:'dict[str|tuple[str,str]|tuple[str]|None,int]' = {None:len(disjunction_list)}
unary_ops:'dict[str|tuple[str,str]|tuple[str]|None,int]' = {None:len(disjunction_list)}

for priority, (nary, ops) in enumerate(disjunction_list):
    nary_ops = binary_ops if nary else unary_ops
    for op in ops:
        nary_ops[op] = priority
binary_keys = binary_ops.keys()
unary_keys = unary_ops.keys()


@dataclass
class root_djn:
    next:'unary_djn|binary_djn|prim_djn|None'=None

@dataclass
class unary_djn:
    op:str
    prev:'root_djn|unary_djn|prim_djn'
    next:'unary_djn|prim_djn|None'=None

    def join(self,p:parser):
        if isinstance(self.next, unary_djn):
            self.next.join(p)
        if isinstance(self.next, prim_djn):
            self.next.prim = unary_op_n(self.op, self.next.prim)
            self.next.prev = self.prev
            self.prev.next = self.next
        else: p.syntax_error(f"no prim_node after unary operator '{self.op}'")

@dataclass
class binary_djn(unary_djn):
    op:str
    prev:'prim_djn'
    next:'unary_djn|prim_djn|None'=None
    
    def join(self, p:parser):
        if isinstance(self.next, unary_djn):
            self.next.join(p)

@dataclass
class prim_djn:
    prim:tree_node
    prev:'root_djn|unary_djn|binary_djn'
    next:'unary_djn|binary_djn|None'=None

def disjunction_r(p:parser):
    opnodemap:'dict[tuple[int,int],unary_djn|binary_djn]' = {}
    prev_root_unary = root = root_djn()
    idx = [0]
    while unop := p.next2ops(unary_keys):
        prev_root_unary = unary_djn(unop, prev_root_unary)
        opnodemap[unary_ops[unop],uidx] = prev_root_unary; uidx -= 1

    unop_err = unop and f"no primary found after unary operator '{unop}'"
    if prim := p.rules(primary_r, err=unop_err):
        prev_prim = prim_djn(prim, prev_root_unary)

        bidx = 0
        while biop := p.next2ops(binary_keys):
            prev_binary = binary_djn(biop, prev_prim)
            opnodemap[binary_ops[unop],bidx] = prev_binary; bidx += 1
            biop_err = f"no primary found after binary operator '{biop}'"

            while unop := p.next2ops(unary_keys):
                prev_binary = unary_djn(unop, prev_binary)
                opnodemap[unary_ops[unop],uidx] = prev_binary; uidx -= 1
            
            prim = p.rules(primary_r, err=biop_err)
            prev_prim = prim_djn(prim, prev_binary)

        priorities = list(opnodemap.keys())
        priorities.sort()

        for node in priorities: opnodemap[node].join(p)
        if isinstance(root.next, prim_djn):
            return root.next.prim

def primary_r(p:parser):
    # TODO
    return atom

def atom(p:parser): return (
    p.nexttok(idftok)
    or
    p.nexttok(numtok)
    or
    p.nextop('True','False','None','...')
    or
    strings_r(p)
    or
    tuple_group_genexp_r(p)
    or
    list_listcomp_r(p)
    or
    dict_set_dictcomp_setcomp_r(p))

def test():
    p = parser('test.py', 
        "a - b / c ** d // h is not g"
        "% i != j == k and l or m or n")
    p.nexttok(tabtok)
    r = p.rule(disjunction)
    print(r)

@todo
def strings_r(p:parser): pass

@todo
def tuple_group_genexp_r(p:parser): pass

@todo
def list_listcomp_r(p:parser): pass

@todo
def dict_set_dictcomp_setcomp_r(p:parser): pass

test()
