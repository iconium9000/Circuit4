# cyparsefuns.py
from dataclasses import dataclass
from cyparser import parser, indent_tracking, todo
import cylexer as lex
import cytree

def file_r(p:parser):
    with indent_tracking(p, True):
        if tok := p.nexttok(lex.tabtok):
            p.indent = tok.slen
            r = p.rule(statements_r)
            p.nexttok(lex.endtok, "failed to reach end of file")
            return r

def statements_r(p:parser):
    def getstmts():
        while r := p.rule(statement_r):
            if isinstance(r, cytree.statements_n):
                yield from r.exprs
            else: yield r
    if args := tuple(getstmts()):
        if len(args) == 1: return args[0]
        return cytree.statements_n(args)

def statement_r(p:parser):
    if tab := p.gettok(lex.tabtok):
        if tab.slen > p.indent: p.error("unexpected indent before statement")
        elif tab.slen == p.indent: p.next()
    return p.rule(compound_stmt_r) or p.rule(simple_stmts_r)

def compound_stmt_r(p:parser):
    if op := p.nextop(compound_stmt_map.keys()):
        return p.rule_err(compound_stmt_map[op.str], f'"{op.str}" invalid syntax')

def simple_stmts_r(p:parser):
    def getstmts():
        while r := p.rule(simple_stmt_r):
            yield r
            if not p.nextop({';'}): break
    if args := tuple(getstmts()):
        if len(args) == 1: return args[0]
        return cytree.statements_n(args)

def simple_stmt_r(p:parser):
    if op := p.nextop(simple_stmt_map.keys()):
        return p.rule_err(simple_stmt_map[op.str], f'"{op.str}" invalid syntax')
    return p.rule(assignment_r) or p.rule(star_expressions_r)

def identifier_r(p:parser):
    if name := p.nexttok(lex.idftok):
        return cytree.identifier_n(name.str)

def star_expression_r(p:parser):
    return p.nextop({'*'}) and p.rule(bitwise_or_r)

def star_target_r(p:parser):
    if not p.nextop({'*'}):
        return p.rule(target_with_star_atom_r)
    elif p.getop({'*'}):
        p.error("second '*' tokens not supported here")
    elif r := p.rule(target_with_star_atom_r):
        return cytree.star_n(r)

def star_targets_r(p:parser):
    def gettargets():
        if r := p.rule(star_target_r):
            yield r
            while p.nextop({','}) and (r := p.rule(star_target_r)):
                yield r
    if args := tuple(gettargets()):
        return cytree.targets_n(args)

def v_single_target_r(p:parser):
    with indent_tracking(p, False):
        if not (p.nextop({'('}) and (r := p.rule(single_target_r))):
           return
    p.nextop({')'}, "no ')' after single_target")
    return r

def target_with_star_atom_r(p:parser): return (
    p.rule(single_subscript_attribute_target_r)
    or
    p.rule(identifier_r)
    or
    p.rule(star_atom_r))

def p_target_with_star_atom_r(p:parser):
    if not p.getop({'('}): return
    with indent_tracking(p, False):
        p.next()
        r = p.rule(target_with_star_atom_r)
    return p.nextop({')'}) and r

def p_star_targets_tuple_seq_r(p:parser):
    if not p.getop({'('}): return
    with indent_tracking(p, False):
        p.next()
        r = p.rule(star_targets_tuple_seq_r)
    if p.nextop({')'}): return r or cytree.tuple_n(tuple())

def star_atom_r(p:parser): return (
    p.rule(p_target_with_star_atom_r)
    or
    p.rule(p_star_targets_tuple_seq_r)
    or
    p.rule(star_targets_list_seq_r))

def star_targets_tuple_seq_r(p:parser):
    def gettargets():
        if (r := p.rule(star_target_r)) and (op := p.nextop({','})):
            yield r
            while op and (r := p.rule(star_target_r)):
                yield r
                op = p.nextop({','})
    if args := tuple(gettargets()):
        return cytree.tuple_n(args)

def star_targets_list_seq_r(p:parser):
    def gettargets():
        op = p.next() # assume '['
        while op and (r := p.rule(star_target_r)):
            yield r
            op = p.nextop({','})
    if not p.getop({'['}): return
    with indent_tracking(p, False):
        r = cytree.list_n(tuple(gettargets()))
    return p.nextop({']'}) and r

def single_target_r(p:parser): return (
    p.rule(single_subscript_attribute_target_r)
    or
    p.rule(identifier_r)
    or
    p.rule(v_single_target_r))

@todo
def p_arguments_r(p:parser):
    p.next() # assume '('
    pass


def primary_r(p:parser):
    def get_primary_r(p:parser):
        if tok.str == '.':
            p.next()
            if n := p.nexttok(lex.idftok):
                return cytree.attribute_ref_n(r, n.str)
        elif tok.str == '[':
            if s := p.rule(slices_r):
                return cytree.subscript_n(r, s)
        elif n := p.rule(genexp_r) or p.rule(p_arguments_r):
            return cytree.call_n(r, n)
    if r_next := p.rule(atom_r):
        r = r_next
        t_next = p.getop({'.','[','('})
        if not t_next: return r
        tok = t_next
        while (r_next := p.rule(get_primary_r)):
            tok = p.getop({'.','[','('})
            r = r_next
        return tok and r

def t_primary_r(p:parser):
    def get_primary_r(p:parser):
        if tok.str == '.':
            p.next()
            if n := p.nexttok(lex.idftok):
                return cytree.attribute_ref_n(r, n.str)
        elif tok.str == '[':
            if s := p.rule(slices_r):
                return cytree.subscript_n(r, s)
        elif n := p.rule(genexp_r) or p.rule(p_arguments_r):
            return cytree.call_n(r, n)
    if ((r_next := p.rule(atom_r))
    and
    (tok := p.getop({'.','[','('}))):
        r = r_next
        while (
            (r_next := p.rule(get_primary_r))
            and
            (tok := p.getop({'.','[','('}))
        ): r = r_next
        return tok and r

def single_subscript_attribute_target_r(p:parser):
    if r := p.rule(t_primary_r):
        op:lex.opstok = p.nextop({'.','['})
        if op.str == '.':
            n = p.nexttok(lex.idftok, "expected identifier after '.' operator")
            r = cytree.attribute_ref_n(r, n.str)
        else: # TODO
            s = p.rule_err(slices_r, "syntax error with slice rule")
            r = cytree.subscript_n(r, s)
        if not p.nextop({'.','[','('}):
            return r

def named_assignment_r(p:parser):
    target = (p.rule(identifier_r)
        or
        p.rule(v_single_target_r)
        or
        p.rule(single_subscript_attribute_target_r))
    if target and p.nextop({':'}):
        hint = p.rule_err(expression_r, "no hint after ':' operator")
        n = cytree.hint_n(target, hint)
        if p.nextop({'='}):
            expr = p.rule_err(annotated_rhs, "no annotated_rhs after '=' operrator")
            return cytree.assignment_n(expr, (n,))
        return n

def target_assign_r(p:parser):
    if (r := p.rule(star_targets_r)) and p.nextop({'='}):
        return r

def annotated_rhs(p:parser): return (
    p.rule(yield_expr_r)
    or
    p.rule(star_expressions_r))

def assignment_list_r(p:parser):
    def gettargets():
        while target := p.rule(target_assign_r):
            yield target
    if targets := tuple(gettargets()):
        expr = p.rule_err(annotated_rhs, "no expression after '=' operator")
        return cytree.assignment_n(expr, targets)

augassign_ops = {'+=','-=','*=','@=','/=','%=','&=','|=','^=','<<=','>>=','**=','//=',}
def augassign_r(p:parser):
    if (target := p.rule(single_target_r)) and (op := p.nextop(augassign_ops)):
        expr = p.rule_err(annotated_rhs, f"expected argument after '{op.str}' operator")
        return cytree.binary_op_n(op.str, target, expr)

def assignment_r(p:parser): return (
    p.rule(named_assignment_r)
    or
    p.rule(assignment_list_r)
    or
    p.rule(augassign_r))

def star_expressions_r(p:parser):
    if r := p.rule(star_expression_r) or p.rule(expression_r):
        def getexprs(r:cytree.tree_node):
            while r and p.nextop({','}):
                yield r
                r = p.rule(star_expression_r) or p.rule(expression_r)
        if args := tuple(getexprs()):
            return cytree.tuple_n(args)
        return r

@todo
def return_stmt_r(p:parser):
    pass # assumes previous tok was 'return' op
@todo
def import_name_r(p:parser):
    pass # assumes previous tok was 'import' op
@todo
def import_from_r(p:parser):
    pass # assumes previous tok was 'import' op
@todo
def raise_stmt_r(p:parser):
    pass # assumes previous tok was 'raise' op
@todo
def import_stmt_r(p:parser):
    pass # assumes previous tok was 'import' op
@todo
def pass_stmt_r(p:parser):
    pass # assumes previous tok was 'pass' op

def yield_expr_r(p:parser):
    return p.nextop({'yield'}) and p.rule(yield_stmt_r)

def yield_stmt_r(p:parser):
    # assumes previous tok was 'yield' op
    if p.nextop({'from'}):
        r = p.rule_err(expression_r, f"no expression after 'yield from' operator")
        r = cytree.star_n(r)
    else: r = p.rule(star_expressions_r) or cytree.bool_n(None)
    return cytree.yield_n(r)

@todo
def assert_stmt_r(p:parser):
    pass # assumes previous tok was 'assert' op
@todo
def break_stmt_r(p:parser):
    pass # assumes previous tok was 'break' op
@todo
def continue_stmt_r(p:parser):
    pass # assumes previous tok was 'continue' op
@todo
def global_stmt_r(p:parser):
    pass # assumes previous tok was 'global' op
@todo
def nonlocal_stmt_r(p:parser):
    pass # assumes previous tok was 'nonlocal' op

simple_stmt_map = {
    'return': return_stmt_r,
    'import': import_name_r,
    'import': import_from_r,
    'raise': raise_stmt_r,
    'import': import_stmt_r,
    'pass': pass_stmt_r,
    'yield': yield_stmt_r,
    'assert': assert_stmt_r,
    'break': break_stmt_r,
    'continue': continue_stmt_r,
    'global': global_stmt_r,
    'nonlocal': nonlocal_stmt_r,
}

@todo
def function_def_r(p:parser): pass

def if_stmt_r(p:parser):
    def getblocks():
        # assumes previous tok was 'if' op
        if_test = p.rule_err(named_expression_r, "missing 'if case'")
        p.nextop({':'}, "missing ':'")
        if_block = p.rule_err(block_r, "missing if block")
        yield cytree.if_expr_n(if_test, if_block)

        while p.nextop({'elif'}):
            elif_test = p.rule_err(named_expression_r, "missing 'elif case'")
            p.nextop({':'}, "missing ':")
            elif_block = p.rule_err(block_r, "missing elif block")
            yield cytree.if_expr_n(elif_test, elif_block)

        if p.nextop('else'):
            p.nextop({':'}, "missing ':")
            else_block = p.rule_err(block_r, "missing else block")
            yield else_block

    return cytree.or_block_n(tuple(getblocks()))

@todo
def class_def_r(p:parser):
    pass # assumes previous tok was 'class' op
@todo
def with_stmt_r(p:parser):
    pass # assumes previous tok was 'with' op
@todo
def for_stmt_r(p:parser):
    pass # assumes previous tok was 'for' op
@todo
def try_stmt_r(p:parser):
    pass # assumes previous tok was 'try' op
@todo
def while_stmt_r(p:parser):
    pass # assumes previous tok was 'while' op
@todo
def match_stmt_r(p:parser):
    pass # assumes previous tok was 'match' op

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

def assignment_expression_r(p:parser):
    if (name := p.rule(identifier_r)) and p.nextop({':='}):
        expr = p.rule_err(expression_r, "no expression after ':=' operator")
        return cytree.assignment_n(expr, (name,))

def named_expression_r(p:parser):
    return p.rule(assignment_expression_r) or p.rule(expression_r)

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
            return cytree.or_block_n(cytree.if_expr_n(if_test, if_body), else_body)
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
        return cytree.or_block_n(args)

def conjunction_r(p:parser):
    def getconjs():
        if a := p.rule(inversion_r):
            yield a
            while p.nextop({'and'}):
                yield p.rule_err(inversion_r, "no conjunction after 'and' operator")
    if args := tuple(getconjs()):
        if len(args) == 1:
            return args[0]
        return cytree.and_block_n(args)

def inversion_r(p:parser):
    if p.nextop({'not'}):
        return cytree.unary_op_n('not', p.rule_err(inversion_r, "no inversion after 'not' operator"))
    return p.rule(comparison_r)

def comparison_op_r(p:parser):
    if op := p.nextop({'is','not','in','>', '>=', '<', '<=', '!=', '=='}):
        if op.str == 'is':
            if p.nextop('not'):
                return lex.opstok('is not', len('is not'), op.tidx, op.lnum, op.lidx)
            return op
        elif op.str != 'not':
            return op
        elif p.nextop({'in'}):
            return lex.opstok('not in', len('not in'), op.tidx, op.lnum, op.lidx)

def comparison_r(p:parser):

    def getcomps():
        while r := p.rule(comparison_op_r):
            op:lex.opstok = r.node
            yield op.str, p.rule_err(bitwise_or_r, f"no bitwise_or after operator")

    if expr := p.rule(bitwise_or_r):
        if comps := tuple(getcomps()):
            return cytree.compare_n(expr, comps)
        return expr

bitwise_op_priority = {
    '@':0, '%':0, '//':0, '/':0, '*':0,
    '+':1, '-':1, '<<':2, '>>':2,
    '&':3, '&':4, '^':5, '|':6 }

@dataclass
class fact_bit_fn:
    fact:cytree.tree_node
    prev:'op_bit_fn|None' = None
    next:'op_bit_fn|None' = None

class op_bit_fn:
    def __init__(self, op:str, prev:fact_bit_fn, f:cytree.tree_node):
        self.op = op
        self.prev = prev
        prev.next = self
        self.next = fact_bit_fn(f, self)

    def join(self):
        # a    +    b    -          ...
        # prev self next next.next

        self.prev.fact = cytree.binary_op_n(self.op, self.prev.fact, self.next.fact)
        self.prev.next = self.next.next
        if self.next.next:
            self.next.next.prev = self.prev

def bitwise_or_r(p:parser):
    if f := p.rule(factor_r):
        f_node = root = fact_bit_fn(f, 0)
        idx = 0
        opmap:dict[tuple[int,int],op_bit_fn] = {}
        keys = bitwise_op_priority.keys()
        while op := p.nextop(keys):
            f = p.rule_err(factor_r, f"no factor after '{op.str}' operator")
            op_node = op_bit_fn(op.str, f_node, f)
            f_node = op_node.next
            opmap[bitwise_op_priority[op.str], idx] = op_node
            idx += 1

        keys = list(opmap.keys()); keys.sort()
        for key in keys: opmap[key].join()
        return root.fact

def factor_r(p:parser):
    if op := p.nextop({'+','-','~'}):
        return cytree.unary_op_n(op.str, p.rule_err(factor_r, f"no factor after '{op.str}' operator"))
    return p.rule(power_r)

def power_r(p:parser):
    if a := p.rule(await_primary_r):
        if p.nextop({'**'}):
            b = p.rule_err(factor_r, "no factor after '**' operator")
            return cytree.binary_op_n('**', a, b)
        return a

def await_primary_r(p:parser):
    if p.nextop({'await'}):
        return cytree.await_n(p.rule_err(primary_r), f"no primary after 'await' operator")
    return p.rule(primary_r)

def slice_r(p:parser):
    a1 = p.rule(expression_r)
    if p.nextop({':'}):
        a2 = p.rule(expression_r)
        a3 = p.nextop({':'}) and p.rule(expression_r)
        return cytree.slice_n(a1,a2,a3)

def slices_r(p:parser):
    def getslices(r:cytree.tree_node):
        op = r
        while r:
            yield r
            r = op and (p.rule(slice_r) or p.rule(named_expression_r))
            op = r and p.nextop({','})
        if r: yield r
    with indent_tracking(p, False):
        p.next() # assume '['
        r = p.rule(slice_r) or p.rule(named_expression_r)
        if not r: return
        elif op := p.getop({','}):
            r = cytree.tuple_n(tuple(getslices(r)))
    p.nextop({']'}, "expected ']' after slices")
    return r

def number_r(p:parser):
    if tok := p.nexttok(lex.numtok):
        return cytree.number_n(tok.str)

def bool_ellipsis_r(p:parser):
    if op := p.nextop({'True','False','None','...'}):
        if op.str == '...': return cytree.ellipsis_n()
        return cytree.bool_n(
            True if op.str == 'True' else
            False if op.str == 'False' else
            None)

def strings_r(p:parser):
    def getstrs():
        while tok := p.nexttok(lex.strtok): yield tok.str
    if p.gettok(lex.strtok): return cytree.string_n(tuple(getstrs()))

def star_named_expression_r(p:parser):
    if p.nextop({'*'}):
        r = p.rule(bitwise_or_r)
        return r and cytree.star_n(r)
    return p.rule(named_expression_r)

def star_named_expression_gr(p:parser):    
    op = True
    while op and (r := p.rule(star_named_expression_r)):
        yield r; op = p.nextop({','})

def tuple_r(p:parser):
    with indent_tracking(p, False):
        p.next() # assume '('
        r = p.rule(star_named_expression_r)
        if not p.nextop({','}): return
        t = r, *star_named_expression_gr(p)
    return p.nextop({')'}) and cytree.tuple_n(t)

def group_r(p:parser):
    with indent_tracking(p, False):
        p.next() # assume '('
        r = p.rule(yield_expr_r) or p.rule(named_expression_r)
    return p.nextop({')'}) and r

def for_if_clauses_ir(i:cytree.tree_node):
    def if_clause_r(p:parser):
        if p.nextop({'if'}) and (test := p.rule(disjunction_r)):
            r = p.rule(for_clause_r) or p.rule(if_clause_r) or i
            return cytree.if_expr_n(test, r)

    def for_clause_r(p:parser):
        fail = False
        if ((op := p.nextop({'async','for'}))
        and
        (op.str == 'for' or p.nextop({'for'}))
        and
        (t := p.rule(star_targets_r))
        and
        p.nextop({'in'})
        and
        (fail := True)
        and
        (i := p.rule(disjunction_r))):
            e = p.rule(for_clause_r) or p.rule(if_clause_r) or i
            r = cytree.for_expr_n(t, i, e)
            if op.str == 'async':
                return cytree.async_n(r)
            return r
        if fail: p.error("expected disjunction after 'in' operator")
    return for_clause_r

def genexp_r(p:parser):
    with indent_tracking(p, False):
        p.next() # assume '('
        i = p.rule(assignment_expression_r)
        if not i:
            i = p.rule(expression_r)
            if not i or p.getop({':='}): return
        r = p.rule(for_if_clauses_ir(cytree.yield_n(i)))
    if r and p.nextop({')'}):
        return cytree.generator_n(r)

def tuple_group_genexp_r(p:parser):
    if not p.getop({'('}): return
    return p.rule(tuple_r) or p.rule(group_r) or p.rule(genexp_r)

def list_r(p:parser):
    with indent_tracking(p, False):
        p.next() # assume '['
        t = tuple(star_named_expression_gr(p))
    return p.nextop({']'}) and cytree.list_n(t)

def listcomp_r(p:parser):
    with indent_tracking(p, False):
        p.next() # assume '['
        i = p.rule(named_expression_r)
        if not i: return
        i = cytree.yield_n(i)
        r = p.rule(for_if_clauses_ir(i))
    if r and p.nextop({']'}):
        g = cytree.generator_n(r)
        t = cytree.star_n(g),
        return cytree.list_n(t)

def list_listcomp_r(p:parser):
    return p.rule(list_r) or p.rule(listcomp_r)

@todo
def dict_set_dictcomp_setcomp_r(p:parser): pass

atom_map = {
    '(': tuple_group_genexp_r,
    '[': list_listcomp_r,
    '{': dict_set_dictcomp_setcomp_r,
}

def atom_r(p:parser):
    if op := p.getop({'(','{','['}):
        return p.rule(atom_map[op.str])
    return (p.rule(identifier_r)
        or
        p.rule(number_r)
        or
        p.rule(bool_ellipsis_r)
        or
        p.rule(strings_r))
