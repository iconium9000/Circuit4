# cyparsefuns.py
from cyparser import *

def file_r(p:parser):
    with indent_tracking(p, True):
        if tok := p.nexttok(tabtok):
            p.indent = tok.slen
            r = p.rule(statements_r)
            p.nexttok(endtok, "failed to reach end of file")
            return r

def statements_r(p:parser):
    def getstmts():
        while r := p.rule(statement_r):
            if isinstance(r, statements_n):
                yield from r.exprs
            else: yield r
    if args := tuple(getstmts()):
        if len(args) == 1: return args[0]
        return statements_n(args)

def statement_r(p:parser):
    if p.gettok(tabtok): return
    return p.rule(compound_stmt_r) or p.rule(simple_stmts_r)

def compound_stmt_r(p:parser):
    if op := p.nextop(compound_stmt_map.keys()):
        return p.rule_err(compound_stmt_map[op.str], f'"{op.str}" invalid syntax')

@todo
def simple_stmts_r(p:parser): pass

@todo
def function_def_r(p:parser): pass

def if_stmt_r(p:parser):

    def getblocks():
        if_test = p.rule_err(named_expression_r, "missing 'if case'")
        p.nextop({':'}, "missing ':'")
        if_block = p.rule_err(block_r, "missing if block")
        yield if_expr_n(if_test, if_block)

        while p.nextop({'elif'}):
            elif_test = p.rule_err(named_expression_r, "missing 'elif case'")
            p.nextop({':'}, "missing ':")
            elif_block = p.rule_err(block_r, "missing elif block")
            yield if_expr_n(elif_test, elif_block)

        if p.nextop('else'):
            p.nextop({':'}, "missing ':")
            else_block = p.rule_err(block_r, "missing else block")
            yield else_block

    return or_block_n(tuple(getblocks()))

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
    if (name_tok := p.nexttok(idftok)) and p.nextop({':='}):
        expr = p.rule_err(expression_r, "no expression after ':=' operator")
        return assignment_n(expr, (name_tok,))

def named_expression_r(p:parser):
    return p.rule(assignment_expression) or p.rule(expression_r)

@todo
def block_r(p:parser): pass

def expression_r(p:parser):
    if p.nextop({'lambda'}):
        return p.rule_err(lambdadef_r, "missing lambda body")
    elif if_body := p.rule(disjunction_r):
        if p.nextop({'if'}):
            if_test = p.rule_err(disjunction_r, "missing if body")
            p.nextop({'else'}, sys="missing 'else' token")
            else_body = p.rule_err(expression_r, "missing else body")
            return or_block_n(if_expr_n(if_test, if_body), else_body)
        return if_body

@todo
def lambdadef_r(p:parser): pass

def disjunction_r(p:parser):
    def getconjs():
        if a := p.rule(conjunction_r):
            yield a
            while p.nextop({'or'}):
                yield p.rule_err(conjunction_r, "no conjunction after 'or' operator")
    if args := list(getconjs()):
        if len(args) == 1:
            return args[0]
        return or_block_n(args)

def conjunction_r(p:parser):
    def getconjs():
        if a := p.rule(inversion_r):
            yield a
            while p.nextop({'and'}):
                yield p.rule_err(inversion_r, "no conjunction after 'and' operator")
    if args := tuple(getconjs()):
        if len(args) == 1:
            return args[0]
        return and_block_n(args)

def inversion_r(p:parser):
    if p.nextop({'not'}):
        return unary_op_n('not', p.rule_err(inversion_r, "no inversion after 'not' operator"))
    return p.rule(comparison_r)


def comparison_op_r(p:parser):
    if op := p.nextop({'is','not','in','>', '>=', '<', '<=', '!=', '=='}):
        if op.str == 'is':
            if p.nextop('not'):
                return opstok('is not', len('is not'), op.tidx, op.lnum, op.lidx)
            return op
        elif op.str != 'not':
            return op
        elif p.nextop({'in'}):
            return opstok('not in', len('not in'), op.tidx, op.lnum, op.lidx)

def comparison_r(p:parser):

    def getcomps():
        while r := p.rule(comparison_op_r):
            op:opstok = r.node
            yield op.str, p.rule_err(bitwise_or_r, f"no bitwise_or after operator")

    if expr := p.rule(bitwise_or_r):
        if comps := tuple(getcomps()):
            return compare_n(expr, comps)
        return expr

bitwise_op_priority = {
    '@':0, '%':0, '//':0, '/':0, '*':0,
    '+':1, '-':1, '<<':2, '>>':2,
    '&':3, '&':4, '^':5, '|':6 }

@dataclass
class fact_bit_n:
    fact:tree_node
    prev:'op_bit_n|None' = None
    next:'op_bit_n|None' = None

class op_bit_n:
    def __init__(self, op:str, prev:fact_bit_n, f:tree_node):
        self.op = op
        self.prev = prev
        prev.next = self
        self.next = fact_bit_n(f, self)

    def join(self):
        # a    +    b    -          ...
        # prev self next next.next

        self.prev.fact = binary_op_n(self.op, self.prev.fact, self.next.fact)
        self.prev.next = self.next.next
        if self.next.next:
            self.next.next.prev = self.prev

def bitwise_or_r(p:parser):
    if f := p.rule(factor_r):
        f_node = root = fact_bit_n(f, 0)
        idx = 0
        opmap:dict[tuple[int,int],op_bit_n] = {}
        keys = bitwise_op_priority.keys()
        while op := p.nextop(keys):
            f = p.rule_err(factor_r, f"no factor after '{op.str}' operator")
            op_node = op_bit_n(op.str, f_node, f)
            f_node = op_node.next
            opmap[bitwise_op_priority[op.str], idx] = op_node
            idx += 1

        keys = list(opmap.keys()); keys.sort()
        for key in keys: opmap[key].join()
        return root.fact

def factor_r(p:parser):
    if op := p.nextop({'+','-','~'}):
        return unary_op_n(op.str, p.rule_err(factor_r, f"no factor after '{op.str}' operator"))
    return p.rule(power_r)

def power_r(p:parser):
    if a := p.rule(await_primary_r):
        if p.nextop({'**'}):
            b = p.rule_err(factor_r, "no factor after '**' operator")
            return binary_op_n('**', a, b)
        return a

def await_primary_r(p:parser):
    if p.nextop({'await'}):
        return await_n(p.rule_err(primary_r), f"no primary after 'await' operator")
    return p.rule(primary_r)

def primary_r(p:parser):
    # TODO
    return p.rule(atom)

def atom(p:parser): return (
    p.nexttok(idftok)
    or
    p.nexttok(numtok)
    or
    p.nextop({'True','False','None','...'})
    or
    p.rule(strings_r)
    or
    p.rule(tuple_group_genexp_r)
    or
    p.rule(list_listcomp_r)
    or
    p.rule(dict_set_dictcomp_setcomp_r))

@todo
def strings_r(p:parser): pass

@todo
def tuple_group_genexp_r(p:parser): pass

@todo
def list_listcomp_r(p:parser): pass

@todo
def dict_set_dictcomp_setcomp_r(p:parser): pass

