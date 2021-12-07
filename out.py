from bnfsupport import *
def invalid_double_starred_kvpairs():
  raise NotImplementedError
def ENDMARKER():(act("ENDMARKER"))
def NEWLINE():(act("NEWLINE"))
def NAME():(act("NAME"))
def TYPE_COMMENT():(act("TYPE_COMMENT"))
def ASYNC():(act("ASYNC"))
def AWAIT():(act("AWAIT"))
def INDENT():(act("INDENT"))
def DEDENT():(act("DEDENT"))
def NUMBER():(act("NUMBER"))
def STRING():(act("STRING"))
def file():
  with lst():
    optional(idf(statements))
    idf(ENDMARKER)
def interactive():(idf(statement_newline))
def eval():
  with lst():
    idf(expressions)
    rep0(idf(NEWLINE))
    idf(ENDMARKER)
def func_type():
  with lst():
    op('(')
    optional(idf(type_expressions))
    op(')')
    op('->')
    idf(expression)
    rep0(idf(NEWLINE))
    idf(ENDMARKER)
def fstring():(idf(star_expressions))
def type_expressions():
  with tryor():
    with lst():
      with rep1():
        with lst():
          idf(expression)
          op(',')
      op(',')
      op('*')
      idf(expression)
      op(',')
      op('**')
      idf(expression)
    with lst():
      with rep1():
        with lst():
          idf(expression)
          op(',')
      op(',')
      op('*')
      idf(expression)
    with lst():
      with rep1():
        with lst():
          idf(expression)
          op(',')
      op(',')
      op('**')
      idf(expression)
    with lst():
      op('*')
      idf(expression)
      op(',')
      op('**')
      idf(expression)
    with lst():
      op('*')
      idf(expression)
    with lst():
      op('**')
      idf(expression)
    with rep1():
      with lst():
        idf(expression)
        op(',')
def statements():(rep1(idf(statement)))
def statement():
  with tryor():
    idf(compound_stmt)
    idf(simple_stmts)
def statement_newline():
  with tryor():
    with lst():
      idf(compound_stmt)
      idf(NEWLINE)
    idf(simple_stmts)
    idf(NEWLINE)
    idf(ENDMARKER)
def simple_stmts():
  with tryor():
    with lst():
      idf(simple_stmt)
      exclusion(op(';'))
      idf(NEWLINE)
    with lst():
      with rep1():
        with lst():
          idf(simple_stmt)
          op(';')
      optional(op(';'))
      idf(NEWLINE)
def simple_stmt():
  with tryor():
    idf(assignment)
    idf(star_expressions)
    idf(return_stmt)
    idf(import_stmt)
    idf(raise_stmt)
    op('pass')
    idf(del_stmt)
    idf(yield_stmt)
    idf(assert_stmt)
    op('break')
    op('continue')
    idf(global_stmt)
    idf(nonlocal_stmt)
def compound_stmt():
  with tryor():
    idf(function_def)
    idf(if_stmt)
    idf(class_def)
    idf(with_stmt)
    idf(for_stmt)
    idf(try_stmt)
    idf(while_stmt)
    idf(match_stmt)
def assignment():
  with tryor():
    with lst():
      idf(NAME)
      op(':')
      idf(expression)
      with optional():
        with lst():
          op('=')
          idf(annotated_rhs)
    with lst():
      with tryor():
        with lst():
          op('(')
          idf(single_target)
          op(')')
        idf(single_subscript_attribute_target)
      op(':')
      idf(expression)
      with optional():
        with lst():
          op('=')
          idf(annotated_rhs)
    with lst():
      with rep1():
        with lst():
          idf(star_targets)
          op('=')
      with tryor():
        idf(yield_expr)
        idf(star_expressions)
      exclusion(op('='))
      optional(idf(TYPE_COMMENT))
    with lst():
      idf(single_target)
      with tilde():
        idf(augassign)
        with tryor():
          idf(yield_expr)
          idf(star_expressions)
def augassign():
  with tryor():
    op('+=')
    op('-=')
    op('*=')
    op('@=')
    op('/=')
    op('%=')
    op('&=')
    op('|=')
    op('^=')
    op('<<=')
    op('>>=')
    op('**=')
    op('//=')
def global_stmt():
  with lst():
    op('global')
    with rep1():
      with lst():
        idf(NAME)
        op(',')
def nonlocal_stmt():
  with lst():
    op('nonlocal')
    with rep1():
      with lst():
        idf(NAME)
        op(',')
def yield_stmt():(idf(yield_expr))
def assert_stmt():
  with lst():
    op('assert')
    idf(expression)
    with optional():
      with lst():
        op(',')
        idf(expression)
def del_stmt():
  with lst():
    op('del')
    idf(del_targets)
    with endswith():
      with tryor():
        op(';')
        idf(NEWLINE)
def import_stmt():
  with tryor():
    idf(import_name)
    idf(import_from)
def import_name():
  with lst():
    op('import')
    idf(dotted_as_names)
def import_from():
  with tryor():
    with lst():
      op('from')
      with rep0():
        with tryor():
          op('.')
          op('...')
      idf(dotted_name)
      op('import')
      idf(import_from_targets)
    with lst():
      op('from')
      with rep1():
        with tryor():
          op('.')
          op('...')
      op('import')
      idf(import_from_targets)
def import_from_targets():
  with tryor():
    with lst():
      op('(')
      idf(import_from_as_names)
      optional(op(','))
      op(')')
    with lst():
      idf(import_from_as_names)
      exclusion(op(','))
    op('*')
def import_from_as_names():
  with rep1():
    with lst():
      idf(import_from_as_name)
      op(',')
def import_from_as_name():
  with lst():
    idf(NAME)
    with optional():
      with lst():
        op('as')
        idf(NAME)
def dotted_as_names():
  with rep1():
    with lst():
      idf(dotted_as_name)
      op(',')
def dotted_as_name():
  with lst():
    idf(dotted_name)
    with optional():
      with lst():
        op('as')
        idf(NAME)
def dotted_name():
  with tryor():
    with lst():
      idf(dotted_name)
      op('.')
      idf(NAME)
    idf(NAME)
def if_stmt():
  with tryor():
    with lst():
      op('if')
      idf(named_expression)
      op(':')
      idf(block)
      idf(elif_stmt)
    with lst():
      op('if')
      idf(named_expression)
      op(':')
      idf(block)
      optional(idf(else_block))
def elif_stmt():
  with tryor():
    with lst():
      op('elif')
      idf(named_expression)
      op(':')
      idf(block)
      idf(elif_stmt)
    with lst():
      op('elif')
      idf(named_expression)
      op(':')
      idf(block)
      optional(idf(else_block))
def else_block():
  with lst():
    op('else')
    op(':')
    idf(block)
def while_stmt():
  with lst():
    op('while')
    idf(named_expression)
    op(':')
    idf(block)
    optional(idf(else_block))
def for_stmt():
  with tryor():
    with lst():
      op('for')
      idf(star_targets)
      with tilde():
        op('in')
        idf(star_expressions)
      op(':')
      optional(idf(TYPE_COMMENT))
      idf(block)
      optional(idf(else_block))
    with lst():
      op('async')
      op('for')
      idf(star_targets)
      with tilde():
        op('in')
        idf(star_expressions)
      op(':')
      optional(idf(TYPE_COMMENT))
      idf(block)
      optional(idf(else_block))
def with_stmt():
  with tryor():
    with lst():
      op('with')
      op('(')
      with rep1():
        with lst():
          idf(with_item)
          op(',')
      question(op(','))
      op(')')
      op(':')
      idf(block)
    with lst():
      op('with')
      with rep1():
        with lst():
          idf(with_item)
          op(',')
      op(':')
      optional(idf(TYPE_COMMENT))
      idf(block)
    with lst():
      op('async')
      op('with')
      op('(')
      with rep1():
        with lst():
          idf(with_item)
          op(',')
      question(op(','))
      op(')')
      op(':')
      idf(block)
    with lst():
      op('async')
      op('with')
      with rep1():
        with lst():
          idf(with_item)
          op(',')
      op(':')
      optional(idf(TYPE_COMMENT))
      idf(block)
def with_item():
  with tryor():
    with lst():
      idf(expression)
      op('as')
      idf(star_target)
      with endswith():
        with tryor():
          op(',')
          op(')')
          op(':')
    idf(expression)
def try_stmt():
  with tryor():
    with lst():
      op('try')
      op(':')
      idf(block)
      idf(finally_block)
    with lst():
      op('try')
      op(':')
      idf(block)
      rep1(idf(except_block))
      optional(idf(else_block))
      optional(idf(finally_block))
def except_block():
  with tryor():
    with lst():
      op('except')
      idf(expression)
      with optional():
        with lst():
          op('as')
          idf(NAME)
      op(':')
      idf(block)
    with lst():
      op('except')
      op(':')
      idf(block)
def finally_block():
  with lst():
    op('finally')
    op(':')
    idf(block)
def match_stmt():
  with lst():
    op("match")
    idf(subject_expr)
    op(':')
    idf(NEWLINE)
    idf(INDENT)
    rep1(idf(case_block))
    idf(DEDENT)
def subject_expr():
  with tryor():
    with lst():
      idf(star_named_expression)
      op(',')
      question(idf(star_named_expressions))
    idf(named_expression)
def case_block():
  with lst():
    op("case")
    idf(patterns)
    question(idf(guard))
    op(':')
    idf(block)
def guard():
  with lst():
    op('if')
    idf(named_expression)
def patterns():
  with tryor():
    idf(open_sequence_pattern)
    idf(pattern)
def pattern():
  with tryor():
    idf(as_pattern)
    idf(or_pattern)
def as_pattern():
  with lst():
    idf(or_pattern)
    op('as')
    idf(pattern_capture_target)
def or_pattern():
  with rep1():
    with lst():
      idf(closed_pattern)
      op('|')
def closed_pattern():
  with tryor():
    idf(literal_pattern)
    idf(capture_pattern)
    idf(wildcard_pattern)
    idf(value_pattern)
    idf(group_pattern)
    idf(sequence_pattern)
    idf(mapping_pattern)
    idf(class_pattern)
def literal_pattern():
  with tryor():
    with lst():
      idf(signed_number)
      with exclusion():
        with tryor():
          op('+')
          op('-')
    idf(complex_number)
    idf(strings)
    op('None')
    op('True')
    op('False')
def literal_expr():
  with tryor():
    with lst():
      idf(signed_number)
      with exclusion():
        with tryor():
          op('+')
          op('-')
    idf(complex_number)
    idf(strings)
    op('None')
    op('True')
    op('False')
def complex_number():
  with tryor():
    with lst():
      idf(signed_real_number)
      op('+')
      idf(imaginary_number)
    with lst():
      idf(signed_real_number)
      op('-')
      idf(imaginary_number)
def signed_number():
  with tryor():
    idf(NUMBER)
    with lst():
      op('-')
      idf(NUMBER)
def signed_real_number():
  with tryor():
    idf(real_number)
    with lst():
      op('-')
      idf(real_number)
def real_number():(idf(NUMBER))
def imaginary_number():(idf(NUMBER))
def capture_pattern():(idf(pattern_capture_target))
def pattern_capture_target():
  with lst():
    exclusion(op("_"))
    idf(NAME)
    with exclusion():
      with tryor():
        op('.')
        op('(')
        op('=')
def wildcard_pattern():(op("_"))
def value_pattern():
  with lst():
    idf(attr)
    with exclusion():
      with tryor():
        op('.')
        op('(')
        op('=')
def attr():
  with lst():
    idf(name_or_attr)
    op('.')
    idf(NAME)
def name_or_attr():
  with tryor():
    idf(attr)
    idf(NAME)
def group_pattern():
  with lst():
    op('(')
    idf(pattern)
    op(')')
def sequence_pattern():
  with tryor():
    with lst():
      op('[')
      question(idf(maybe_sequence_pattern))
      op(']')
    with lst():
      op('(')
      question(idf(open_sequence_pattern))
      op(')')
def open_sequence_pattern():
  with lst():
    idf(maybe_star_pattern)
    op(',')
    question(idf(maybe_sequence_pattern))
def maybe_sequence_pattern():
  with lst():
    with rep1():
      with lst():
        idf(maybe_star_pattern)
        op(',')
    question(op(','))
def maybe_star_pattern():
  with tryor():
    idf(star_pattern)
    idf(pattern)
def star_pattern():
  with tryor():
    with lst():
      op('*')
      idf(pattern_capture_target)
    with lst():
      op('*')
      idf(wildcard_pattern)
def mapping_pattern():
  with tryor():
    with lst():
      op('{')
      op('}')
    with lst():
      op('{')
      idf(double_star_pattern)
      question(op(','))
      op('}')
    with lst():
      op('{')
      idf(items_pattern)
      op(',')
      idf(double_star_pattern)
      question(op(','))
      op('}')
    with lst():
      op('{')
      idf(items_pattern)
      question(op(','))
      op('}')
def items_pattern():
  with rep1():
    with lst():
      idf(key_value_pattern)
      op(',')
def key_value_pattern():
  with lst():
    with tryor():
      idf(literal_expr)
      idf(attr)
    op(':')
    idf(pattern)
def double_star_pattern():
  with lst():
    op('**')
    idf(pattern_capture_target)
def class_pattern():
  with tryor():
    with lst():
      idf(name_or_attr)
      op('(')
      op(')')
    with lst():
      idf(name_or_attr)
      op('(')
      idf(positional_patterns)
      question(op(','))
      op(')')
    with lst():
      idf(name_or_attr)
      op('(')
      idf(keyword_patterns)
      question(op(','))
      op(')')
    with lst():
      idf(name_or_attr)
      op('(')
      idf(positional_patterns)
      op(',')
      idf(keyword_patterns)
      question(op(','))
      op(')')
def positional_patterns():
  with rep1():
    with lst():
      idf(pattern)
      op(',')
def keyword_patterns():
  with rep1():
    with lst():
      idf(keyword_pattern)
      op(',')
def keyword_pattern():
  with lst():
    idf(NAME)
    op('=')
    idf(pattern)
def return_stmt():
  with lst():
    op('return')
    optional(idf(star_expressions))
def raise_stmt():
  with tryor():
    with lst():
      op('raise')
      idf(expression)
      with optional():
        with lst():
          op('from')
          idf(expression)
    op('raise')
def function_def():
  with tryor():
    with lst():
      idf(decorators)
      idf(function_def_raw)
    idf(function_def_raw)
def function_def_raw():
  with tryor():
    with lst():
      op('def')
      idf(NAME)
      op('(')
      optional(idf(params))
      op(')')
      with optional():
        with lst():
          op('->')
          idf(expression)
      op(':')
      optional(idf(func_type_comment))
      idf(block)
    with lst():
      op('async')
      op('def')
      idf(NAME)
      op('(')
      optional(idf(params))
      op(')')
      with optional():
        with lst():
          op('->')
          idf(expression)
      op(':')
      optional(idf(func_type_comment))
      idf(block)
def func_type_comment():
  with tryor():
    with lst():
      idf(NEWLINE)
      idf(TYPE_COMMENT)
      with endswith():
        with lst():
          idf(NEWLINE)
          idf(INDENT)
    idf(TYPE_COMMENT)
def params():(idf(parameters))
def parameters():
  with tryor():
    with lst():
      idf(slash_no_default)
      rep0(idf(param_no_default))
      rep0(idf(param_with_default))
      optional(idf(star_etc))
    with lst():
      idf(slash_with_default)
      rep0(idf(param_with_default))
      optional(idf(star_etc))
    with lst():
      rep1(idf(param_no_default))
      rep0(idf(param_with_default))
      optional(idf(star_etc))
    with lst():
      rep1(idf(param_with_default))
      optional(idf(star_etc))
    idf(star_etc)
def slash_no_default():
  with tryor():
    with lst():
      rep1(idf(param_no_default))
      op('/')
      op(',')
    with lst():
      rep1(idf(param_no_default))
      op('/')
      endswith(op(')'))
def slash_with_default():
  with tryor():
    with lst():
      rep0(idf(param_no_default))
      rep1(idf(param_with_default))
      op('/')
      op(',')
    with lst():
      rep0(idf(param_no_default))
      rep1(idf(param_with_default))
      op('/')
      endswith(op(')'))
def star_etc():
  with tryor():
    with lst():
      op('*')
      idf(param_no_default)
      rep0(idf(param_maybe_default))
      optional(idf(kwds))
    with lst():
      op('*')
      op(',')
      rep1(idf(param_maybe_default))
      optional(idf(kwds))
    idf(kwds)
def kwds():
  with lst():
    op('**')
    idf(param_no_default)
def param_no_default():
  with tryor():
    with lst():
      idf(param)
      op(',')
      question(idf(TYPE_COMMENT))
    with lst():
      idf(param)
      question(idf(TYPE_COMMENT))
      endswith(op(')'))
def param_with_default():
  with tryor():
    with lst():
      idf(param)
      idf(default)
      op(',')
      question(idf(TYPE_COMMENT))
    with lst():
      idf(param)
      idf(default)
      question(idf(TYPE_COMMENT))
      endswith(op(')'))
def param_maybe_default():
  with tryor():
    with lst():
      idf(param)
      question(idf(default))
      op(',')
      question(idf(TYPE_COMMENT))
    with lst():
      idf(param)
      question(idf(default))
      question(idf(TYPE_COMMENT))
      endswith(op(')'))
def param():
  with lst():
    idf(NAME)
    question(idf(annotation))
def annotation():
  with lst():
    op(':')
    idf(expression)
def default():
  with lst():
    op('=')
    idf(expression)
def decorators():
  with rep1():
    with lst():
      op('@')
      idf(named_expression)
      idf(NEWLINE)
def class_def():
  with tryor():
    with lst():
      idf(decorators)
      idf(class_def_raw)
    idf(class_def_raw)
def class_def_raw():
  with lst():
    op('class')
    idf(NAME)
    with optional():
      with lst():
        op('(')
        optional(idf(arguments))
        op(')')
    op(':')
    idf(block)
def block():
  with tryor():
    with lst():
      idf(NEWLINE)
      idf(INDENT)
      idf(statements)
      idf(DEDENT)
    idf(simple_stmts)
def star_expressions():
  with tryor():
    with lst():
      idf(star_expression)
      with rep1():
        with lst():
          op(',')
          idf(star_expression)
      optional(op(','))
    with lst():
      idf(star_expression)
      op(',')
    idf(star_expression)
def star_expression():
  with tryor():
    with lst():
      op('*')
      idf(bitwise_or)
    idf(expression)
def star_named_expressions():
  with lst():
    with rep1():
      with lst():
        idf(star_named_expression)
        op(',')
    optional(op(','))
def star_named_expression():
  with tryor():
    with lst():
      op('*')
      idf(bitwise_or)
    idf(named_expression)
def assignment_expression():
  with lst():
    idf(NAME)
    with tilde():
      op(':=')
      idf(expression)
def named_expression():
  with tryor():
    idf(assignment_expression)
    with lst():
      idf(expression)
      exclusion(op(':='))
def annotated_rhs():
  with tryor():
    idf(yield_expr)
    idf(star_expressions)
def expressions():
  with tryor():
    with lst():
      idf(expression)
      with rep1():
        with lst():
          op(',')
          idf(expression)
      optional(op(','))
    with lst():
      idf(expression)
      op(',')
    idf(expression)
def expression():
  with tryor():
    with lst():
      idf(disjunction)
      op('if')
      idf(disjunction)
      op('else')
      idf(expression)
    idf(disjunction)
    idf(lambdef)
def lambdef():
  with lst():
    op('lambda')
    optional(idf(lambda_params))
    op(':')
    idf(expression)
def lambda_params():(idf(lambda_parameters))
def lambda_parameters():
  with tryor():
    with lst():
      idf(lambda_slash_no_default)
      rep0(idf(lambda_param_no_default))
      rep0(idf(lambda_param_with_default))
      optional(idf(lambda_star_etc))
    with lst():
      idf(lambda_slash_with_default)
      rep0(idf(lambda_param_with_default))
      optional(idf(lambda_star_etc))
    with lst():
      rep1(idf(lambda_param_no_default))
      rep0(idf(lambda_param_with_default))
      optional(idf(lambda_star_etc))
    with lst():
      rep1(idf(lambda_param_with_default))
      optional(idf(lambda_star_etc))
    idf(lambda_star_etc)
def lambda_slash_no_default():
  with tryor():
    with lst():
      rep1(idf(lambda_param_no_default))
      op('/')
      op(',')
    with lst():
      rep1(idf(lambda_param_no_default))
      op('/')
      endswith(op(':'))
def lambda_slash_with_default():
  with tryor():
    with lst():
      rep0(idf(lambda_param_no_default))
      rep1(idf(lambda_param_with_default))
      op('/')
      op(',')
    with lst():
      rep0(idf(lambda_param_no_default))
      rep1(idf(lambda_param_with_default))
      op('/')
      endswith(op(':'))
def lambda_star_etc():
  with tryor():
    with lst():
      op('*')
      idf(lambda_param_no_default)
      rep0(idf(lambda_param_maybe_default))
      optional(idf(lambda_kwds))
    with lst():
      op('*')
      op(',')
      rep1(idf(lambda_param_maybe_default))
      optional(idf(lambda_kwds))
    idf(lambda_kwds)
def lambda_kwds():
  with lst():
    op('**')
    idf(lambda_param_no_default)
def lambda_param_no_default():
  with tryor():
    with lst():
      idf(lambda_param)
      op(',')
    with lst():
      idf(lambda_param)
      endswith(op(':'))
def lambda_param_with_default():
  with tryor():
    with lst():
      idf(lambda_param)
      idf(default)
      op(',')
    with lst():
      idf(lambda_param)
      idf(default)
      endswith(op(':'))
def lambda_param_maybe_default():
  with tryor():
    with lst():
      idf(lambda_param)
      question(idf(default))
      op(',')
    with lst():
      idf(lambda_param)
      question(idf(default))
      endswith(op(':'))
def lambda_param():(idf(NAME))
def disjunction():
  with tryor():
    with lst():
      idf(conjunction)
      with rep1():
        with lst():
          op('or')
          idf(conjunction)
    idf(conjunction)
def conjunction():
  with tryor():
    with lst():
      idf(inversion)
      with rep1():
        with lst():
          op('and')
          idf(inversion)
    idf(inversion)
def inversion():
  with tryor():
    with lst():
      op('not')
      idf(inversion)
    idf(comparison)
def comparison():
  with tryor():
    with lst():
      idf(bitwise_or)
      rep1(idf(compare_op_bitwise_or_pair))
    idf(bitwise_or)
def compare_op_bitwise_or_pair():
  with tryor():
    idf(eq_bitwise_or)
    idf(noteq_bitwise_or)
    idf(lte_bitwise_or)
    idf(lt_bitwise_or)
    idf(gte_bitwise_or)
    idf(gt_bitwise_or)
    idf(notin_bitwise_or)
    idf(in_bitwise_or)
    idf(isnot_bitwise_or)
    idf(is_bitwise_or)
def eq_bitwise_or():
  with lst():
    op('==')
    idf(bitwise_or)
def noteq_bitwise_or():
  with lst():
    op('!=')
    idf(bitwise_or)
def lte_bitwise_or():
  with lst():
    op('<=')
    idf(bitwise_or)
def lt_bitwise_or():
  with lst():
    op('<')
    idf(bitwise_or)
def gte_bitwise_or():
  with lst():
    op('>=')
    idf(bitwise_or)
def gt_bitwise_or():
  with lst():
    op('>')
    idf(bitwise_or)
def notin_bitwise_or():
  with lst():
    op('not')
    op('in')
    idf(bitwise_or)
def in_bitwise_or():
  with lst():
    op('in')
    idf(bitwise_or)
def isnot_bitwise_or():
  with lst():
    op('is')
    op('not')
    idf(bitwise_or)
def is_bitwise_or():
  with lst():
    op('is')
    idf(bitwise_or)
def bitwise_or():
  with tryor():
    with lst():
      idf(bitwise_or)
      op('|')
      idf(bitwise_xor)
    idf(bitwise_xor)
def bitwise_xor():
  with tryor():
    with lst():
      idf(bitwise_xor)
      op('^')
      idf(bitwise_and)
    idf(bitwise_and)
def bitwise_and():
  with tryor():
    with lst():
      idf(bitwise_and)
      op('&')
      idf(shift_expr)
    idf(shift_expr)
def shift_expr():
  with tryor():
    with lst():
      idf(shift_expr)
      op('<<')
      idf(sum)
    with lst():
      idf(shift_expr)
      op('>>')
      idf(sum)
    idf(sum)
def sum():
  with tryor():
    with lst():
      idf(sum)
      op('+')
      idf(term)
    with lst():
      idf(sum)
      op('-')
      idf(term)
    idf(term)
def term():
  with tryor():
    with lst():
      idf(term)
      op('*')
      idf(factor)
    with lst():
      idf(term)
      op('/')
      idf(factor)
    with lst():
      idf(term)
      op('//')
      idf(factor)
    with lst():
      idf(term)
      op('%')
      idf(factor)
    with lst():
      idf(term)
      op('@')
      idf(factor)
    idf(factor)
def factor():
  with tryor():
    with lst():
      op('+')
      idf(factor)
    with lst():
      op('-')
      idf(factor)
    with lst():
      op('~')
      idf(factor)
    idf(power)
def power():
  with tryor():
    with lst():
      idf(await_primary)
      op('**')
      idf(factor)
    idf(await_primary)
def await_primary():
  with tryor():
    with lst():
      idf(AWAIT)
      idf(primary)
    idf(primary)
def primary():
  with tryor():
    with lst():
      idf(primary)
      op('.')
      idf(NAME)
    with lst():
      idf(primary)
      idf(genexp)
    with lst():
      idf(primary)
      op('(')
      optional(idf(arguments))
      op(')')
    with lst():
      idf(primary)
      op('[')
      idf(slices)
      op(']')
    idf(atom)
def slices():
  with tryor():
    with lst():
      idf(slice)
      exclusion(op(','))
    with lst():
      with rep1():
        with lst():
          idf(slice)
          op(',')
      optional(op(','))
def slice():
  with tryor():
    with lst():
      optional(idf(expression))
      op(':')
      optional(idf(expression))
      with optional():
        with lst():
          op(':')
          optional(idf(expression))
    idf(named_expression)
def atom():
  with tryor():
    idf(NAME)
    op('True')
    op('False')
    op('None')
    idf(strings)
    idf(NUMBER)
    with tryor():
      idf(tuple)
      idf(group)
      idf(genexp)
    with tryor():
      idf(list)
      idf(listcomp)
    with tryor():
      idf(dict)
      idf(set)
      idf(dictcomp)
      idf(setcomp)
    op('...')
def strings():(rep1(idf(STRING)))
def list():
  with lst():
    op('[')
    optional(idf(star_named_expressions))
    op(']')
def listcomp():
  with lst():
    op('[')
    idf(named_expression)
    idf(for_if_clauses)
    op(']')
def tuple():
  with lst():
    op('(')
    with optional():
      with lst():
        idf(star_named_expression)
        op(',')
        optional(idf(star_named_expressions))
    op(')')
def group():
  with lst():
    op('(')
    with tryor():
      idf(yield_expr)
      idf(named_expression)
    op(')')
def genexp():
  with lst():
    op('(')
    with tryor():
      idf(assignment_expression)
      with lst():
        idf(expression)
        exclusion(op(':='))
    idf(for_if_clauses)
    op(')')
def set():
  with lst():
    op('{')
    idf(star_named_expressions)
    op('}')
def setcomp():
  with lst():
    op('{')
    idf(named_expression)
    idf(for_if_clauses)
    op('}')
def dict():
  with tryor():
    with lst():
      op('{')
      optional(idf(double_starred_kvpairs))
      op('}')
    with lst():
      op('{')
      idf(invalid_double_starred_kvpairs)
      op('}')
def dictcomp():
  with lst():
    op('{')
    idf(kvpair)
    idf(for_if_clauses)
    op('}')
def double_starred_kvpairs():
  with lst():
    with rep1():
      with lst():
        idf(double_starred_kvpair)
        op(',')
    optional(op(','))
def double_starred_kvpair():
  with tryor():
    with lst():
      op('**')
      idf(bitwise_or)
    idf(kvpair)
def kvpair():
  with lst():
    idf(expression)
    op(':')
    idf(expression)
def for_if_clauses():(rep1(idf(for_if_clause)))
def for_if_clause():
  with tryor():
    with lst():
      op('async')
      op('for')
      idf(star_targets)
      with tilde():
        op('in')
        idf(disjunction)
      with rep0():
        with lst():
          op('if')
          idf(disjunction)
    with lst():
      op('for')
      idf(star_targets)
      with tilde():
        op('in')
        idf(disjunction)
      with rep0():
        with lst():
          op('if')
          idf(disjunction)
def yield_expr():
  with tryor():
    with lst():
      op('yield')
      op('from')
      idf(expression)
    with lst():
      op('yield')
      optional(idf(star_expressions))
def arguments():
  with lst():
    idf(args)
    optional(op(','))
    endswith(op(')'))
def args():
  with tryor():
    with lst():
      with rep1():
        with lst():
          with tryor():
            idf(starred_expression)
            with lst():
              with tryor():
                idf(assignment_expression)
                with lst():
                  idf(expression)
                  exclusion(op(':='))
              exclusion(op('='))
          op(',')
      with optional():
        with lst():
          op(',')
          idf(kwargs)
    idf(kwargs)
def kwargs():
  with tryor():
    with lst():
      with rep1():
        with lst():
          idf(kwarg_or_starred)
          op(',')
      op(',')
      with rep1():
        with lst():
          idf(kwarg_or_double_starred)
          op(',')
    with rep1():
      with lst():
        idf(kwarg_or_starred)
        op(',')
    with rep1():
      with lst():
        idf(kwarg_or_double_starred)
        op(',')
def starred_expression():
  with lst():
    op('*')
    idf(expression)
def kwarg_or_starred():
  with tryor():
    with lst():
      idf(NAME)
      op('=')
      idf(expression)
    idf(starred_expression)
def kwarg_or_double_starred():
  with tryor():
    with lst():
      idf(NAME)
      op('=')
      idf(expression)
    with lst():
      op('**')
      idf(expression)
def star_targets():
  with tryor():
    with lst():
      idf(star_target)
      exclusion(op(','))
    with lst():
      idf(star_target)
      with rep0():
        with lst():
          op(',')
          idf(star_target)
      optional(op(','))
def star_targets_list_seq():
  with lst():
    with rep1():
      with lst():
        idf(star_target)
        op(',')
    optional(op(','))
def star_targets_tuple_seq():
  with tryor():
    with lst():
      idf(star_target)
      with rep1():
        with lst():
          op(',')
          idf(star_target)
      optional(op(','))
    with lst():
      idf(star_target)
      op(',')
def star_target():
  with tryor():
    with lst():
      op('*')
      with lst():
        exclusion(op('*'))
        idf(star_target)
    idf(target_with_star_atom)
def target_with_star_atom():
  with tryor():
    idf(single_subscript_attribute_target)
    with tryor():
      idf(NAME)
      idf(star_atom)
def star_atom():
  with tryor():
    with lst():
      op('(')
      idf(target_with_star_atom)
      op(')')
    with lst():
      op('(')
      optional(idf(star_targets_tuple_seq))
      op(')')
    with lst():
      op('[')
      optional(idf(star_targets_list_seq))
      op(']')
def v_single_target():
  with lst():
    op('(')
    idf(single_target)
    op(')')
def single_target():
  with tryor():
    idf(single_subscript_attribute_target)
    idf(NAME)
    idf(v_single_target)
def single_subscript_attribute_target():
  with tryor():
    with lst():
      idf(t_primary)
      op('.')
      idf(NAME)
      exclusion(idf(t_lookahead))
    with lst():
      idf(t_primary)
      op('[')
      idf(slices)
      op(']')
      exclusion(idf(t_lookahead))
def del_targets():
  with lst():
    with rep1():
      with lst():
        idf(del_target)
        op(',')
    optional(op(','))
def del_target():
  with tryor():
    idf(single_subscript_attribute_target)
    idf(del_t_atom)
def del_t_atom():
  with tryor():
    idf(NAME)
    with lst():
      op('(')
      idf(del_target)
      op(')')
    with lst():
      op('(')
      optional(idf(del_targets))
      op(')')
    with lst():
      op('[')
      optional(idf(del_targets))
      op(']')
def t_primary():
  with tryor():
    with lst():
      idf(t_primary)
      op('.')
      idf(NAME)
      endswith(idf(t_lookahead))
    with lst():
      idf(t_primary)
      op('[')
      idf(slices)
      op(']')
      endswith(idf(t_lookahead))
    with lst():
      idf(t_primary)
      idf(genexp)
      endswith(idf(t_lookahead))
    with lst():
      idf(t_primary)
      op('(')
      optional(idf(arguments))
      op(')')
      endswith(idf(t_lookahead))
    with lst():
      idf(atom)
      endswith(idf(t_lookahead))
def t_lookahead():
  with tryor():
    op('(')
    op('[')
    op('.')
