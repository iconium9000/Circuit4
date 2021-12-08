# cyparsefuns.py
from dataclasses import dataclass
from typing import Callable
from cyparser import parser, todo
import cylexer as lex
from cythonlexer import tabtok
import cytree as tree
from out import genexp

def file_r(p:parser):
    if tok := p.nexttok(lex.tabtok):
        p.indent = tok.slen
        r = p.rule(statements_r)
        p.nexttok(lex.endtok, "failed to reach end of file")
        return r

@todo
def block_r(p:parser):
    indent = p.indent
    def statements_block_r(p:parser):
        if ((t := p.nexttok(lex.tabtok))
        and
        t.slen > indent):
            p.indent = indent
    r = p.rule(statements_block_r)
    if r: return r
    else: p.indent = indent
    

def statements_r(p:parser):
    def getstmts():
        while r := p.rule(statement_r):
            if isinstance(r, tree.statements_n):
                yield from r.exprs
            else: yield r
    if args := tuple(getstmts()):
        if len(args) == 1: return args[0]
        return tree.statements_n(args)

def statement_r(p:parser):
    return p.rule(compound_stmt_r) or p.rule(simple_stmts_r)

def compound_stmt_r(p:parser):
    if op := p.nextop(compound_stmt_map.keys()):
        return p.rule_err(compound_stmt_map[op.str],
            f'"{op.str}" invalid syntax')

def simple_stmts_r(p:parser):
    def getstmts():
        while r := p.rule(simple_stmt_r):
            yield r
            if not p.nextop({';'}): break
    if args := tuple(getstmts()):
        if len(args) == 1: return args[0]
        return tree.statements_n(args)

def simple_stmt_r(p:parser):
    if op := p.nextop(simple_stmt_map.keys()):
        return p.rule_err(simple_stmt_map[op.str], f'"{op.str}" invalid syntax')
    return p.rule(assignment_r) or p.rule(star_expressions_r)

def identifier_r(p:parser):
    if name := p.nexttok(lex.idftok):
        return tree.identifier_n(name.str)

def star_expression_r(p:parser):
    return p.nextop({'*'}) and p.rule(bitwise_or_r)

def star_target_r(p:parser):
    if not p.nextop({'*'}):
        return p.rule(target_with_star_atom_r)
    elif p.getop({'*'}):
        p.error("second '*' tokens not supported here")
    elif r := p.rule(target_with_star_atom_r):
        return tree.star_n(r)

def star_targets_r(p:parser):
    def gettargets():
        if r := p.rule(star_target_r):
            yield r
            while p.nextop({','}) and (r := p.rule(star_target_r)):
                yield r
    if args := tuple(gettargets()):
        return tree.targets_n(args)

def v_single_target_r(p:parser):
    return p.ignore_tracking('(', single_target_r, ')')

def target_with_star_atom_r(p:parser): return (
    p.rule(single_subscript_attribute_target_r)
    or
    p.rule(identifier_r)
    or
    p.rule(star_atom_r))

def p_target_with_star_atom_r(p:parser):
    return p.ignore_tracking('(', target_with_star_atom_r, ')')

def p_star_targets_tuple_seq_r(p:parser):

    def gen_tuple_seq(r:tree.tree_node):
        yield r
        while r and (r := p.rule(star_target_r)):
            yield r
            r = p.nextop({','})

    def tuple_seq(p:parser):
        r = p.rule(star_target_r)
        if not r: return tree.tuple_n(tuple())
        if not p.nextop({','}): return
        return tree.tuple_n(tuple(gen_tuple_seq(r)))

    return p.ignore_tracking('(', tuple_seq, ')')

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
        return tree.tuple_n(args)

def star_targets_list_seq_r(p:parser):

    def targets_r(p:parser):

        def gen_targets():
            while r := p.rule(star_target_r):
                yield r
                if not p.nextop({','}): break

        if args := tuple(gen_targets()):
            return tree.list_n(args)

    return p.ignore_tracking('[', targets_r, ']')

def single_target_r(p:parser): return (
    p.rule(single_subscript_attribute_target_r)
    or
    p.rule(identifier_r)
    or
    p.rule(v_single_target_r))

def named_assignment_r(p:parser):
    target = (p.rule(identifier_r)
        or
        p.rule(v_single_target_r)
        or
        p.rule(single_subscript_attribute_target_r))
    if target and p.nextop({':'}):
        hint = p.rule_err(expression_r, "no hint after ':' operator")
        n = tree.hint_n(target, hint)
        if p.nextop({'='}):
            expr = p.rule_err(annotated_rhs, "no annotated_rhs after '=' operrator")
            return tree.assignment_n(expr, (n,))
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
        return tree.assignment_n(expr, targets)

augassign_ops = {'+=','-=','*=','@=','/=','%=','&=','|=','^=','<<=','>>=','**=','//=',}
def augassign_r(p:parser):
    if (target := p.rule(single_target_r)) and (op := p.nextop(augassign_ops)):
        expr = p.rule_err(annotated_rhs, f"expected argument after '{op.str}' operator")
        return tree.binary_op_n(op.str, target, expr)

def assignment_r(p:parser): return (
    p.rule(named_assignment_r)
    or
    p.rule(assignment_list_r)
    or
    p.rule(augassign_r))

def star_expressions_r(p:parser):
    if r := p.rule(star_expression_r) or p.rule(expression_r):
        def getexprs(r:tree.tree_node):
            while r and p.nextop({','}):
                yield r
                r = p.rule(star_expression_r) or p.rule(expression_r)
        if args := tuple(getexprs()):
            return tree.tuple_n(args)
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
        r = tree.star_n(r)
    else: r = p.rule(star_expressions_r) or tree.bool_n(None)
    return tree.yield_n(r)

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
        yield tree.if_expr_n(if_test, if_block)

        while p.nextop({'elif'}):
            elif_test = p.rule_err(named_expression_r, "missing 'elif case'")
            p.nextop({':'}, "missing ':")
            elif_block = p.rule_err(block_r, "missing elif block")
            yield tree.if_expr_n(elif_test, elif_block)

        if p.nextop('else'):
            p.nextop({':'}, "missing ':")
            else_block = p.rule_err(block_r, "missing else block")
            yield else_block

    return tree.or_block_n(tuple(getblocks()))

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
        return tree.assignment_n(expr, (name,))

def named_expression_r(p:parser):
    return p.rule(assignment_expression_r) or p.rule(expression_r)

def expression_r(p:parser):
    if p.nextop({'lambda'}):
        return p.rule_err(lambdadef_r, "missing lambda body")
    elif if_body := p.rule(disjunction_r):
        if p.nextop({'if'}):
            if_test = p.rule_err(disjunction_r, "missing if body")
            p.nextop({'else'}, sys="missing 'else' token")
            else_body = p.rule_err(expression_r, "missing else body")
            return tree.or_block_n(tree.if_expr_n(if_test, if_body), else_body)
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
        return tree.or_block_n(args)

def conjunction_r(p:parser):
    def getconjs():
        if a := p.rule(inversion_r):
            yield a
            while p.nextop({'and'}):
                yield p.rule_err(inversion_r, "no conjunction after 'and' operator")
    if args := tuple(getconjs()):
        if len(args) == 1:
            return args[0]
        return tree.and_block_n(args)

def inversion_r(p:parser):
    if p.nextop({'not'}):
        return tree.unary_op_n('not', p.rule_err(inversion_r, "no inversion after 'not' operator"))
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
            return tree.compare_n(expr, comps)
        return expr

bitwise_op_priority = {
    '@':0, '%':0, '//':0, '/':0, '*':0,
    '+':1, '-':1, '<<':2, '>>':2,
    '&':3, '&':4, '^':5, '|':6 }

def bitwise_or_r(p:parser):
    @dataclass
    class fact_bit_fn:
        fact:tree.tree_node
        prev:'op_bit_fn|None' = None
        next:'op_bit_fn|None' = None

    class op_bit_fn:
        def __init__(self, op:str, prev:fact_bit_fn, f:tree.tree_node):
            self.op = op
            self.prev = prev
            prev.next = self
            self.next = fact_bit_fn(f, self)

        def join(self):
            # a    +    b    -          ...
            # prev self next next.next

            self.prev.fact = tree.binary_op_n(self.op, self.prev.fact, self.next.fact)
            self.prev.next = self.next.next
            if self.next.next:
                self.next.next.prev = self.prev

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
        return tree.unary_op_n(op.str, p.rule_err(factor_r, f"no factor after '{op.str}' operator"))
    return p.rule(power_r)

def power_r(p:parser):
    if a := p.rule(await_primary_r):
        if p.nextop({'**'}):
            b = p.rule_err(factor_r, "no factor after '**' operator")
            return tree.binary_op_n('**', a, b)
        return a

def await_primary_r(p:parser):
    if p.nextop({'await'}):
        return tree.await_n(p.rule_err(primary_r), f"no primary after 'await' operator")
    return p.rule(primary_r)

def slice_r(p:parser):
    a1 = p.rule(expression_r)
    if p.nextop({':'}):
        a2 = p.rule(expression_r)
        a3 = p.nextop({':'}) and p.rule(expression_r)
        return tree.slice_n(a1,a2,a3)

def slices_r(p:parser):
    def single_slice_r(p:parser):
        if (r := p.rule(slice_r)) and not p.getop({','}):
            return r
    def gen_tuple_slices():
        while r := p.rule(slice_r):
            yield r
            if not p.nextop(','): break
    if r := p.rule(single_slice_r): return r
    elif args := tuple(gen_tuple_slices):
        return tree.tuple_n(args)

def star_named_expression_r(p:parser):
    if p.nextop({'*'}):
        r = p.rule(bitwise_or_r)
        return r and tree.star_n(r)
    return p.rule(named_expression_r)

def star_named_expression_gr(p:parser):    
    while r := p.rule(star_named_expression_r):
        yield r
        if not p.nextop({','}): break

lookahead_set = {'.','[','('}

def sub_primary_pr(p:parser, a:tree.tree_node):
    if p.tok.str == '.':
        p.next()
        if n := p.nexttok(lex.idftok):
            return tree.attribute_ref_n(a, n.str)
    elif p.tok.str == '[':
        if s := p.rule(slices_r):
            return tree.subscript_n(a, s)
    elif n := p.rule(genexp_r) or p.rule(p_arguments_r):
        return tree.call_n(a, n)

def primary_r(p:parser):
    if a := p.rule(atom_r):
        r = a
        def sub_primary_r(p:parser):
            return p.getop(lookahead_set) and sub_primary_pr(p, r)
        while a := p.rule(sub_primary_r): r = a
        return r

def single_subscript_attribute_target_r(p:parser): 
    if (a := p.rule(atom_r)) and p.getop(lookahead_set):
        r = a
        def t_primary_r(p:parser):
            a = sub_primary_pr(p, r)
            return a and p.getop(lookahead_set) and a
        while a := p.rule(t_primary_r): r = a

def for_if_clauses_ir(i:tree.tree_node):
    def if_clause_r(p:parser):
        if p.nextop({'if'}) and (test := p.rule(disjunction_r)):
            r = p.rule(for_clause_r) or p.rule(if_clause_r) or i
            return tree.if_expr_n(test, r)

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
            r = tree.for_expr_n(t, i, e)
            if op.str == 'async':
                return tree.async_n(r)
            return r
        if fail: p.error("expected disjunction after 'in' operator")
    return for_clause_r

@todo
def args_r(p:parser):
    pass

def arguments_r(p:parser):
    r = p.rule(args_r)
    p.nextop({','})
    return p.getop(')') and r

def p_arguments_r(p:parser):
    return p.ignore_tracking('(', arguments_r, ')')

def genexp_r(p:parser):
    def sub_genexp_r(p:parser):
        i = p.rule(assignment_expression_r)
        if not i:
            i = p.rule(expression_r)
            if not i or p.getop({':='}): return
        r = p.rule(for_if_clauses_ir(tree.yield_n(i)))
        return tree.generator_n(r)
    return p.ignore_tracking('(', sub_genexp_r, ')')


def tuple_group_genexp_r(p:parser):

    def tuple_r(p:parser):
        r = p.rule(star_named_expression_r)
        if not p.nextop({','}): return
        t = r, *star_named_expression_gr(p)
        return tree.tuple_n(t)

    def group_r(p:parser):
        return p.rule(yield_expr_r) or p.rule(named_expression_r)

    return (p.ignore_tracking('(', tuple_r, ')')
            or
            p.ignore_tracking('(', group_r, ')')
            or
            p.rule(genexp_r))

def list_listcomp_r(p:parser):

    def list_r(p:parser):
        t = tuple(star_named_expression_gr(p))
        return tree.list_n(t)

    def listcomp_r(p:parser):
        if ((i := p.rule(named_expression_r))
        and
        (i := tree.yield_n(i))
        and
        (r := p.rule(for_if_clauses_ir(i)))):
            g = tree.generator_n(r)
            t = tree.star_n(g)
            return tree.list_n(t)

    return (p.ignore_tracking('[', list_r, ']')
            or
            p.ignore_tracking('[', listcomp_r, ']'))

@todo
def dict_set_dictcomp_setcomp_r(p:parser): pass

atom_map = {
    '(': tuple_group_genexp_r,
    '[': list_listcomp_r,
    '{': dict_set_dictcomp_setcomp_r,
}

def number_r(p:parser):
    if tok := p.nexttok(lex.numtok):
        return tree.number_n(tok.str)

def bool_ellipsis_r(p:parser):
    if op := p.nextop({'True','False','None','...'}):
        if op.str == '...': return tree.ellipsis_n()
        return tree.bool_n(
            True if op.str == 'True' else
            False if op.str == 'False' else
            None)

def strings_r(p:parser):
    def getstrs():
        while tok := p.nexttok(lex.strtok): yield tok.str
    if p.gettok(lex.strtok): return tree.string_n(tuple(getstrs()))

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
