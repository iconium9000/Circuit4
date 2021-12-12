# cyparsefuns.py
from dataclasses import dataclass
from cyparser import parser, todo
import cylexer as lex
import cytree as tree


############################################################
if "file_r: NEWLINE statements_r ~ ENDMARKER":
    def file_r(p:parser):
        if p.nextnewline() and (r := p.rule(statements_r)):
            p.gettok(lex.endtok, "failed to reach end of file")
            return tree.program_n(r)


############################################################
if """
block_r:
    | NEWLINE ~ INDENT ~ statements_r ~ DEDENT
    | simple_stmts_r
""":
    def block_r(p:parser):
        if p.nextnewline():
            i = p.nextindent()
            if i is None: p.error('no indent')
            r = p.rule_err(statements_r, 'expected statements after indent')
            if p.nextdedent(i) and p.nextnewline(): return r
            else: p.error('no dedent after block')
        else: return p.rule(simple_stmts_r)


############################################################
if "statements_r: statement_r+":
    def statements_r(p:parser):
        if args := tuple(gen_statements(p)):
            if len(args) == 1: return args[0]
            return tree.statements_n(args)

    def gen_statements(p:parser):
        while r := p.rule(statement_r):
            if isinstance(r, tree.statements_n):
                yield from r.exprs
            else: yield r


############################################################
if "statement_r: compound_stmt_r  | simple_stmts_r":
    def statement_r(p:parser):
        if not p.gettok(lex.endtok):
            return (p.rule(compound_stmt_r)
                    or
                    p.rule(simple_stmts_r))


############################################################
if "simple_stmts_r: ';'.simple_stmt_r+ [';'] NEWLINE":
    def simple_stmts_r(p:parser):
        if (args := tuple(gen_simple_stmts(p))) and p.nextnewline():
            if len(args) == 1: return args[0]
            return tree.statements_n(args)

    def gen_simple_stmts(p:parser):
        while r := p.rule(simple_stmt_r):
            yield r
            if not p.nextop({';'}): break


############################################################
if "identifier_r: NAME":
    def identifier_r(p:parser):
        if name := p.nexttok(lex.idftok):
            return tree.idf_n(name.str)


############################################################
if "star_expression_r: '*' bitwise_or_r":
    def star_expression_r(p:parser):
        return p.nextop({'*'}) and p.rule(bitwise_or_r)


############################################################
if """
star_target_r:
    | '*' (!'*' target_with_star_atom)
    | target_with_star_atom_r
""":
    def star_target_r(p:parser):
        if not p.nextop({'*'}):
            return p.rule(target_with_star_atom_r)
        elif p.getop({'*'}): return
        elif r := p.rule(target_with_star_atom_r):
            return tree.iter_target_n(r)


############################################################
if """
star_targets_r:
    | star_target_r !','
    | star_target_r (',' star_target_r )* [',']
""":
    def star_targets_r(p:parser):
        if (r := p.rule(star_target_r)) and not p.nextop({','}):
            return r
        if args := tuple(gen_star_targets(p)):
            return tree.tuple_target_n(args)

    def gen_star_targets(p:parser):
        if r := p.rule(star_target_r):
            yield r
            while p.nextop({','}) and (r := p.rule(star_target_r)):
                yield r


############################################################
if "v_single_target_r: TODO":
    def v_single_target_r(p:parser):
        return p.ignore_tracking('(', single_target_r, ')')


############################################################
if """
target_with_star_atom_r: TODO
    | single_subscript_attribute_target_r
    | identifier_target_r
    | '(' target_with_star_atom_r ')'
    | '(' star_targets_tuple_seq_r ')'
    | '[' star_targets_list_seq_r ']'
""":
    def target_with_star_atom_r(p:parser):
        return (p.rule(single_subscript_attribute_target_r)
                or
                p.rule(identifier_target_r)
                or
                p.rule(p_target_with_star_atom_r)
                or
                p.rule(p_star_targets_tuple_seq_r)
                or
                p.rule(star_targets_list_seq_r))

    def p_target_with_star_atom_r(p:parser):
        return p.ignore_tracking('(', target_with_star_atom_r, ')')


############################################################
if "p_star_targets_tuple_seq_r: TODO":
    def p_star_targets_tuple_seq_r(p:parser):
        return p.ignore_tracking('(', tuple_seq_r, ')')

    def tuple_seq_r(p:parser):
        r = p.rule(star_target_r)
        if not r: return tree.tuple_target_n(tuple())
        if not p.nextop({','}): return
        return tree.tuple_target_n(tuple(gen_tuple_seq(p,r)))

    def gen_tuple_seq(p:parser, r:tree.tree_node):
        yield r
        while r and (r := p.rule(star_target_r)):
            yield r
            r = p.nextop({','})


############################################################
if "star_targets_tuple_seq_r: TODO":
    def star_targets_tuple_seq_r(p:parser):
        if args := tuple(gen_star_targets_tuple_seq(p)):
            return tree.tuple_n(args)

    def gen_star_targets_tuple_seq(p:parser):
        if (r := p.rule(star_target_r)) and (op := p.nextop({','})):
            yield r
            while op and (r := p.rule(star_target_r)):
                yield r
                op = p.nextop({','})


############################################################
if "star_targets_list_seq_r: TODO":
    def star_targets_list_seq_r(p:parser):
        return p.ignore_tracking('[', targets_r, ']')

    def targets_r(p:parser):
        if args := tuple(gen_targets(p)):
            return tree.list_target_n(args)

    def gen_targets(p:parser):
        while r := p.rule(star_target_r):
            yield r
            if not p.nextop({','}): break


############################################################
if "identifier_target_r: NAME":
    def identifier_target_r(p:parser):
        if t := p.nexttok(lex.idftok):
            return tree.idf_target_n(t.str)

############################################################
if """
single_target_r:
    | single_subscript_attribute_target_r
    | identifier_target_r
    | v_single_target_r
""":
    def single_target_r(p:parser):
        return (p.rule(single_subscript_attribute_target_r)
                or
                p.rule(identifier_target_r)
                or
                p.rule(v_single_target_r))


############################################################
if """
name_target_r:
    | identifier_target_r
    | v_single_target_r
    | single_subscript_attribute_target_r
""":
    def name_target_r(p:parser): return(
        p.rule(identifier_target_r)
        or
        p.rule(v_single_target_r)
        or
        p.rule(single_subscript_attribute_target_r))


############################################################
if """
named_assignment_r:
    | name_target_r ':' expression_r ['=' ~ annotated_rhs]
""":
    def named_assignment_r(p:parser):
        if ((t := p.rule(name_target_r))
            and
            p.nextop({':'})
            and
            (h := p.rule(expression_r))):
            n = tree.hint_n(t, h)
            if p.nextop({'='}):
                expr = p.rule_err(annotated_rhs, "no annotated_rhs after '=' operrator")
                return tree.assignment_n(expr, (n,))
            return n


############################################################
if "annotated_rhs: yield_expr_r | star_expressions_r":
    def annotated_rhs(p:parser):
        return (p.rule(yield_expr_r)
                or
                p.rule(star_expressions_r))


############################################################
if "assignment_list_r: (star_targets_r '=')+ ~ annotated_rhs":
    def assignment_list_r(p:parser):
        if targets := tuple(gen_assign_targets(p)):
            expr = p.rule_err(annotated_rhs, "no expression after '=' operator")
            return tree.assignment_n(expr, targets)

    def gen_assign_targets(p:parser):
        while target := p.rule(assign_target_r):
            yield target

    def assign_target_r(p:parser):
        if (r := p.rule(star_targets_r)) and p.nextop({'='}):
            return r


############################################################
if "augassign_r: single_target_r {augassign_op} ~ annotated_rhs":
    def augassign_r(p:parser):
        if (target := p.rule(single_target_r)) and (op := p.nextop(augassign_ops)):
            expr = p.rule_err(annotated_rhs, f"expected argument after '{op.str}' operator")
            return tree.binary_op_n(op.str, target, expr)

    augassign_ops = {'+=','-=','*=','@=','/=','%=','&=','|=','^=','<<=','>>=','**=','//=',}


############################################################
if "assignment_r: named_assignment_r | assignment_list_r | augassign_r":
    def assignment_r(p:parser):
        return (p.rule(named_assignment_r)
                or
                p.rule(assignment_list_r)
                or
                p.rule(augassign_r))


############################################################
if """
star_expressions_r:
    | (star_expression_r | expression_r) !','
    | ','.(star_expression_r | expression_r)+ [',']
""":
    def star_expressions_r(p:parser):
        if r := p.rule(star_expression_r) or p.rule(expression_r):
            if args := tuple(gen_star_expressions(p,r)):
                return tree.tuple_n(args)
            return r

    def gen_star_expressions(p:parser, r:tree.tree_node):
        while r and p.nextop({','}):
            yield r
            r = p.rule(star_expression_r) or p.rule(expression_r)


############################################################
@todo # return_stmt_r: 'return'& TODO
def return_stmt_r(p:parser): pass


############################################################
@todo # import_name_r: 'import'& TODO
def import_name_r(p:parser): pass


############################################################
@todo # import_from_r: 'import'& TODO
def import_from_r(p:parser): pass


############################################################
@todo # raise_stmt_r: 'raise'& TODO
def raise_stmt_r(p:parser): pass


############################################################
@todo # import_stmt_r: 'import'& TODO
def import_stmt_r(p:parser): pass


############################################################
@todo # pass_stmt_r: 'pass'& TODO
def pass_stmt_r(p:parser): pass

############################################################
if "yield_expr_r: 'yield' yield_stmt_r":
    def yield_expr_r(p:parser):
        return p.nextop({'yield'}) and p.rule(yield_stmt_r)

############################################################
if "yield_stmt_r: 'yield'& ['from' ~ expression_r | star_expressions_r]":
    def yield_stmt_r(p:parser):
        if p.nextop({'from'}):
            r = p.rule_err(expression_r, f"no expression after 'yield from' operator")
            r = tree.star_n(r)
        else: r = p.rule(star_expressions_r) or tree.bool_n(None)
        return tree.yield_n(r)


############################################################
@todo # assert_stmt_r: 'assert'& TODO
def assert_stmt_r(p:parser): pass


############################################################
@todo # break_stmt_r: 'break'& TODO
def break_stmt_r(p:parser): pass


############################################################
@todo # continue_stmt_r: 'continue'& TODO
def continue_stmt_r(p:parser): pass


############################################################
@todo # global_stmt_r: 'global'& TODO
def global_stmt_r(p:parser): pass


############################################################
@todo # nonlocal_stmt_r: 'nonlocal'& TODO
def nonlocal_stmt_r(p:parser): pass


############################################################
if """
"simple_stmt_r:":
    | assignment_r
    | star_expressions_r
    | 'return' ~ return_stmt_r
    | 'import' ~ import_stmt_r
    | 'raise' ~ raise_stmt_r
    | 'pass' ~ pass_stmt_r
    | 'del' ~ del_stmt_r
    | 'yield' ~ yield_stmt_r
    | 'assert' ~ assert_stmt_r
    | 'break' ~ break_stmt_r
    | 'continue' ~ continue_stmt_r
    | 'global' ~ global_stmt_r
    | 'nonlocal' ~ nonlocal_stmt_r
""":
    def simple_stmt_r(p:parser):
        if op := p.nextop(simple_stmt_map.keys()):
            return p.rule_err(simple_stmt_map[op.str], f'"{op.str}" invalid syntax')
        return p.rule(assignment_r) or p.rule(star_expressions_r)

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


############################################################
@todo # function_def_r: 'def'& TODO
def function_def_r(p:parser):
    pass # assumes previous tok was 'def' op


############################################################
@todo # class_def_r: 'class'& TODO
def class_def_r(p:parser):
    pass # assumes previous tok was 'class' op


############################################################
if """
decorator_stmt_r:
    | '@'& named_expression NEWLINE ~ decorator_stmt_r
""":
    @todo
    def decorator_stmt_r(p:parser):
        pass # assumes previous tok was '@' op


############################################################
if """
def_stmt_r:
    | '@' ~ decorator_stmt_r
    | 'def' ~ function_def_r
    | 'class' ~ class_def_r
""":
    def def_stmt_r(p:parser):
        if op := p.nextop(def_stmt_ops):
            return p.rule_err(def_stmt_ops[op.str],
                f"no def_stmt after '{op.str}' operator")

def_stmt_ops = {
    '@': decorator_stmt_r,
    'def': function_def_r,
    'class': class_def_r
}


##############################################################
if """
if_stmt_r: if_elif_block_r ['elif' if_stmt_r | 'else' else_block_r]"
if_elif_block_r: ('if' | 'elif')& ~ named_expression ~ ':' ~ block
else_block_r: 'else'& ~ ':' ~ block
""":
    def if_stmt_r(p:parser):
        if_test = p.rule_err(named_expression_r, "missing 'if/elif test'")
        p.nextop({':'}, "missing ':'")
        if_true = p.rule_err(block_r, "missing if block")

        if t := p.nextop({'elif', 'else'}):
            if t.str == 'elif':
                if_false = p.rule(if_stmt_r)
            else:
                if_false = p.rule(else_block_r)
        else: if_false = tree.pass_n()
        return tree.if_n(if_test, if_true, if_false)

    def else_block_r(p:parser):
        p.nextop({':'}, "missing ':")
        return p.rule_err(block_r, "missing else block")

############################################################
@todo # with_stmt_r: 'with'& TODO
def with_stmt_r(p:parser):
    pass # assumes previous tok was 'with' op


############################################################
@todo # for_stmt_r: 'for'& TODO
def for_stmt_r(p:parser):
    pass # assumes previous tok was 'for' op


############################################################
@todo # try_stmt_r: 'try'& TODO
def try_stmt_r(p:parser):
    pass # assumes previous tok was 'try' op


############################################################
@todo # while_stmt_r: 'while'& TODO
def while_stmt_r(p:parser):
    pass # assumes previous tok was 'while' op


############################################################
@todo # match_stmt_r: 'match'& TODO
def match_stmt_r(p:parser):
    pass # assumes previous tok was 'match' op


############################################################
@todo # async_stmt_r: 'async'& TODO
def async_stmt_r(p:parser):
    pass # assumes previous tok was 'async' op


############################################################
if """
"compound_stmt_r:":
    | 'def' ~ function_def_r
    | 'if' ~ if_stmt_r
    | 'class' ~ class_def_r
    | 'with' ~ with_stmt_r
    | 'for' ~ for_stmt_r
    | 'try' ~ try_stmt_r
    | 'while' ~ while_stmt_r
    | 'match' ~ match_stmt_r
""":
    def compound_stmt_r(p:parser):
        if op := p.nextop(compound_stmt_map.keys()):
            err = f'"{op.str}" invalid syntax'
            return p.rule_err(compound_stmt_map[op.str], err)

    compound_stmt_map = {
        '@': decorator_stmt_r,
        'def': function_def_r,
        'class': class_def_r,
        'if': if_stmt_r,
        'async': async_stmt_r,
        'with': with_stmt_r,
        'for': for_stmt_r,
        'try': try_stmt_r,
        'while': while_stmt_r,
        'match': match_stmt_r,
    }


############################################################
if "assignment_expression_r: identifier_r ':=' ~ expression_r":
    def assignment_expression_r(p:parser):
        if (target := p.rule(identifier_target_r)) and p.nextop({':='}):
            expr = p.rule_err(expression_r, "no expression after ':=' operator")
            return tree.assignment_n(expr, (target,))


############################################################
if "named_expression_r: assignment_expression_r | expression_r":
    def named_expression_r(p:parser):
        return p.rule(assignment_expression_r) or p.rule(expression_r)


############################################################
@todo # lambda_def_r: 'lambda'& TODO
def lambda_def_r(p:parser):
    pass # assumes previous tok was 'lambda' op


############################################################
if """
"expression_r:":
    | 'lambda' ~ lambda_def_r
    | disjunction_r ['if' ~ disjunction_r ~ 'else' ~ expression_r]
""":
    def expression_r(p:parser):
        if p.nextop({'lambda'}):
            return p.rule_err(lambda_def_r, "missing lambda body")
        elif if_true := p.rule(disjunction_r):
            if p.nextop({'if'}):
                if_test = p.rule_err(disjunction_r, "missing if body")
                p.nextop({'else'}, sys="missing 'else' token")
                if_false = p.rule_err(expression_r, "missing else body")
                return tree.if_n(if_test, if_true, if_false)
            return if_true


############################################################
if "disjunction_r: 'or'.conjunction_r+":
    def disjunction_r(p:parser):
        if args := list(gen_disjunction(p)):
            if len(args) == 1:
                return args[0]
            return tree.or_block_n(args)

    def gen_disjunction(p:parser):
        if a := p.rule(conjunction_r):
            yield a
            while p.nextop({'or'}):
                yield p.rule_err(conjunction_r, "no conjunction after 'or' operator")


############################################################
if "conjunction_r: 'and'.inversion_r+":
    def conjunction_r(p:parser):
        if args := tuple(gen_conjunction(p)):
            if len(args) == 1:
                return args[0]
            return tree.and_block_n(args)

    def gen_conjunction(p:parser):
        if a := p.rule(inversion_r):
            yield a
            while p.nextop({'and'}):
                yield p.rule_err(inversion_r, "no conjunction after 'and' operator")


############################################################
if "inversion_r: 'not' ~ inversion_r | comparison_r":
    def inversion_r(p:parser):
        if p.nextop({'not'}):
            err = "no inversion after 'not' operator"
            return tree.unary_op_n('not', p.rule_err(inversion_r, err))
        return p.rule(comparison_r)


############################################################
if "comparison_r: bitwise_or_r (comparison_op_r ~ bitwise_or_r)*":
    def comparison_r(p:parser):
        if expr := p.rule(bitwise_or_r):
            if comps := tuple(gen_comparison(p)):
                return tree.compare_n(expr, comps)
            return expr

    def gen_comparison(p:parser):
        while r := p.rule(comparison_op_r):
            op:lex.opstok = r.node
            r = p.rule_err(bitwise_or_r, f"no bitwise_or after operator")
            yield op.str, r

    """
    comparison_op_r:
        | 'is' ['not']
        | 'not' ~ 'in'
        | {comparison_ops}
    """
    def comparison_op_r(p:parser):
        if op := p.nextop(comparison_ops):
            if op.str == 'is':
                if p.nextop('not'):
                    return lex.opstok('is not', len('is not'), op.tidx, op.lnum, op.lidx)
                return op
            elif op.str != 'not':
                return op
            elif p.nextop({'in'}):
                return lex.opstok('not in', len('not in'), op.tidx, op.lnum, op.lidx)

    comparison_ops = {'is','not','in','>', '>=', '<', '<=', '!=', '=='}


############################################################
if """
bitwise_or:
    | bitwise_or '|' bitwise_xor
    | bitwise_xor
# bitwise_xor:
    | bitwise_xor '^' bitwise_and
    | bitwise_and
# bitwise_and:
    | bitwise_and '&' shift_expr
    | shift_expr
# shift_expr:
    | shift_expr '<<' sum
    | shift_expr '>>' sum
    | sum
# sum:
    | sum '+' term
    | sum '-' term
    | term
# term:
    | term '*' factor
    | term '/' factor
    | term '//' factor
    | term '%' factor
    | term '@' factor
    | factor
""":
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

    bitwise_op_priority = {
        '@':0, '%':0, '//':0, '/':0, '*':0,
        '+':1, '-':1, '<<':2, '>>':2,
        '&':3, '&':4, '^':5, '|':6 }

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


############################################################
if """
factor_r: ('+' | '-' | '~') ~ factor_r | power_r
power_r: await_primary_r ['**' ~ factor]
await_primary_r: 'await' ~ primary_r | primary_r
""":
    def factor_r(p:parser):
        if op := p.nextop({'+','-','~'}):
            r = p.rule_err(factor_r, f"no factor after '{op.str}' operator")
            return tree.unary_op_n(op.str, r)
        return p.rule(power_r)

    def power_r(p:parser):
        if a := p.rule(await_primary_r):
            if p.nextop({'**'}):
                b = p.rule_err(factor_r, "no factor after '**' operator")
                return tree.binary_op_n('**', a, b)
            return a

    def await_primary_r(p:parser):
        if p.nextop({'await'}):
            r = p.rule_err(primary_r), f"no primary after 'await' operator"
            return tree.await_n(r)
        return p.rule(primary_r)


############################################################
if "slices_r: TODO":
    def slices_r(p:parser):
        if r := p.rule(single_slice_r): return r
        elif args := tuple(gen_tuple_slices(p)):
            return tree.tuple_n(args)

    def slice_r(p:parser):
        a1 = p.rule(expression_r)
        if p.nextop({':'}):
            a2 = p.rule(expression_r)
            a3 = p.nextop({':'}) and p.rule(expression_r)
            return tree.slice_n(a1,a2,a3)

    def single_slice_r(p:parser):
        if ((r := p.rule(slice_r) or p.rule(named_expression_r))
        and not p.getop({','})): return r

    def gen_tuple_slices(p:parser):
        while r := p.rule(slice_r) or p.rule(named_expression_r):
            yield r
            if not p.nextop(','): break


############################################################
if "star_named_expression_r: TODO":
    def star_named_expression_r(p:parser):
        if p.nextop({'*'}):
            r = p.rule(bitwise_or_r)
            return r and tree.star_n(r)
        return p.rule(named_expression_r)


############################################################
if "star_named_expression_gr: TODO":
    def star_named_expression_gr(p:parser):
        while r := p.rule(star_named_expression_r):
            yield r
            if not p.nextop({','}): break


############################################################
if """
sub_primary_pr:
    | primary& '.' ~ NAME
    | primary& '[' ~ slices ']'
    | primary& &'(' genexp
    | primary& &'(' p_arguments_r
""":
    def sub_primary_pr(p:parser, a:tree.tree_node):
        if p.tok.str == '.':
            p.next()
            if n := p.nexttok(lex.idftok):
                return tree.attribute_ref_n(a, n.str)
            p.error("no identifier after '.' operator")
        elif p.tok.str == '[':
            if s := p.ignore_tracking('[',slices_r,']'):
                return tree.subscript_n(a, s)
            p.error("no slice after '[' operator")
        elif n := p.rule(genexp_r):
            args = tree.arguments_n((n,))
            return tree.call_n(a, args)
        elif args := p.rule(p_arguments_r):
            return tree.call_n(a, args)


############################################################
if """
single_subscript_attribute_target_r:
    | t_primary_r '.' ~ NAME !{lookahead_set}
    | t_primary_r '[' slices ']' !{lookahead_set}
""":
    def single_subscript_attribute_target_r(p:parser):
        if (a := p.rule(t_primary_r)):
            if p.tok.str == '.':
                p.next()
                if n := p.nexttok(lex.idftok):
                    return tree.attribute_target_n(a, n.str)
                p.error("no identifier after '.' operator")
            elif p.tok.str == '[':
                if s := p.ignore_tracking('[',slices_r,']'):
                    return tree.subscript_target_n(a, s)
                p.error("no slice after '[' operator")


############################################################
if "primary_r: atom_r (&{lookahead_set} sub_primary_pr)*":
    def primary_r(p:parser):
        if a := p.rule(atom_r):
            r = a
            def sub_primary_r(p:parser):
                return p.getop(lookahead_set) and sub_primary_pr(p, r)
            while a := p.rule(sub_primary_r): r = a
            return r

    lookahead_set = {'.','[','('}


    "t_primary_r: atom_r &{lookahead_set} (sub_primary_pr &{lookahead_set})*"
    def t_primary_r(p:parser):
        if (a := p.rule(atom_r)) and p.getop(lookahead_set):
            r = a
            def sub_t_primary_r(p:parser):
                if (s := sub_primary_pr(p, r)) and p.getop(lookahead_set):
                    return s
            while a := p.rule(sub_t_primary_r): r = a
            return r

############################################################
if "for_if_clauses_ir: TODO":
    def for_if_clauses_ir(i:tree.tree_node):

        def if_clause_r(p:parser):
            if p.nextop({'if'}) and (test := p.rule(disjunction_r)):
                r = p.rule(for_clause_r) or p.rule(if_clause_r) or i
                return tree.if_n(test, r, tree.continue_n())

        def for_clause_r(p:parser):
            fail = False
            if ((op := p.nextop({'async','for'}))
            and
            (op.str == 'for' or p.nextop({'for'}))
            and
            (target := p.rule(star_targets_r))
            and
            p.nextop({'in'})
            and
            (fail := True)
            and
            (iterable := p.rule(disjunction_r))):
                block = p.rule(for_clause_r) or p.rule(if_clause_r) or i
                r = tree.for_n(target, iterable, block)
                if op.str == 'async':
                    return tree.async_n(r)
                return r
            if fail: p.error("expected disjunction after 'in' operator")

        return for_clause_r


############################################################
if """
"arg_r:":
    | starred_expression_r
    | assignment_expression_r
    | expression_r
    | kwarg_r
    | starred_expression_r
""":
    def arg_r(p:parser):
        return (p.rule(starred_expression_r)
                or
                p.rule(assignment_expression_r)
                or
                p.rule(expression_r)
                or
                p.rule(kwarg_r)
                or
                p.rule(starred_expression_r))


############################################################
if "starred_expression_r: '*' expression_r":
    def starred_expression_r(p:parser):
        if r := p.nextop({'*'}) and expression_r(p):
            return tree.star_n(r)


############################################################
if "double_starred_expression_r: '**' expression_r":
    def double_starred_expression_r(p:parser):
        if r := p.nextop({'**'}) and expression_r(p):
            return tree.kw_star_n(r)


############################################################
if "kwarg_r: NAME '=' ~ expression_r":
    def kwarg_r(p:parser):
        if (i := p.nexttok(lex.idftok)) and p.nextop({'='}):
            e = p.rule_err(expression_r, 'no expression after kwarg')
            return tree.kwarg_n(i.str, e)


############################################################
if "p_arguments_r: '(' [','.arg_r+ [',']] ')'":
    def p_arguments_r(p:parser):
        def gen_args(p:parser):
            while r := p.rule(arg_r):
                yield r
                if not p.nextop(','): break
        def args_r(p:parser):
            return tree.arguments_n(tuple(gen_args(p)))
        return p.ignore_tracking('(', args_r, ')')


############################################################
if "genexp_r: TODO":
    def genexp_r(p:parser):
        def sub_genexp_r(p:parser):
            i = p.rule(assignment_expression_r)
            if not i:
                i = p.rule(expression_r)
                if not i or p.getop({':='}): return
            if r := p.rule(for_if_clauses_ir(tree.yield_n(i))):
                return tree.generator_n(r)
        return p.ignore_tracking('(', sub_genexp_r, ')')


############################################################
if "tuple_group_genexp_r: TODO":
    def tuple_group_genexp_r(p:parser):
        return (p.ignore_tracking('(', tuple_r, ')')
                or
                p.ignore_tracking('(', group_r, ')')
                or
                p.rule(genexp_r))

    def tuple_r(p:parser):
        r = p.rule(star_named_expression_r)
        if not p.nextop({','}): return
        t = r, *star_named_expression_gr(p)
        return tree.tuple_n(t)

    def group_r(p:parser):
        return p.rule(yield_expr_r) or p.rule(named_expression_r)


############################################################
if "list_listcomp_r: TODO":
    def list_listcomp_r(p:parser):
        return (p.ignore_tracking('[', list_r, ']')
                or
                p.ignore_tracking('[', listcomp_r, ']'))

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


############################################################
@todo # dict_set_dictcomp_setcomp_r: TODO
def dict_set_dictcomp_setcomp_r(p:parser): pass


############################################################
if "atom_r: TODO":
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

    atom_map = {
        '(': tuple_group_genexp_r,
        '[': list_listcomp_r,
        '{': dict_set_dictcomp_setcomp_r}

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
