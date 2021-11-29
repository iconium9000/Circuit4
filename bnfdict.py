# bnfdict.py

entry_stack = []
numtabs = 0
def ptabs(tabs, *args):
    print(tabs, *args, file=g_file)


def getlist(args):
    if isinstance(args, str):
        return args, True
    elif not args:
        return '', True
    elif len(args) == 1:
        return getlist(args[0])
    elif len(args) > 2:
        return [getlist(arg)[0] for arg in args], False
    elif len(args) == 2:
        arg0, is0str = getlist(args[0])
        arg1, is1str = getlist(args[1])
        if args[0] in ('or','lst'): return arg1, is1str
        elif is0str and is1str: return f'{arg0}({arg1})', True
        return (arg0, arg1), False

def recprint(args, tab=''):
    assert len(tab) < 30
    args, isstr = getlist(args)
    if isstr: return ptabs(tab, args)
    tok, *args = args
    assert isinstance(tok, str)
    if not tab: ptabs(tab, tok + ':')
    else: ptabs(tab, tok)
    tab += ' '
    for arg in args: recprint(arg, tab)

g_dict = {}
g_tree = {}
g_file = None
def proc(d:dict, entry):
    global g_dict, g_file
    g_dict = d
    with open('out.log', 'w') as g_file:
        idf(entry)
        for entry in g_tree.items():
            recprint(entry)

def idf(entry):
    if entry in entry_stack: return ['inf', entry]
    r = g_tree.get(entry)
    if r: return r
    arg = g_dict.get(entry)
    if arg is None: return ['inf', entry]
    entry_stack.append(entry)
    r = proc_atom(*arg)
    entry_stack.pop()
    assert r
    g_tree[entry] = r
    return ['inf', entry]

def proc_atom(tok, *args):
    r = atommap[tok](*args)
    assert r
    return r

def lst(*args):
    if len(args) == 1:
        return proc_atom(*args[0])
    return ['lst'] + [proc_atom(*arg) for arg in args]
def tryor(*args):
    if len(args) == 1:
        return proc_atom(*args[0])
    return ['or'] + [proc_atom(*arg) for arg in args]

def optional(arg): return ['optional', proc_atom(*arg)]
def rep0(arg): return ['rep0', proc_atom(*arg)]
def rep1(arg): return ['rep1', proc_atom(*arg)]
def op(arg): return ['op', arg]
def exclusion(arg): return ['exclusion', proc_atom(*arg)]
def tilde(arg1, arg2): return ['tilde', proc_atom(*arg1), proc_atom(*arg2)]
def endswith(arg): return ['endswith', proc_atom(*arg)]
def question(arg): return ['question', proc_atom(*arg)]
def act(arg): return ['act', arg]

atommap = {
    'lst': lst,
    'tryor': tryor,
    'optional': optional,
    'idf': idf,
    'rep0': rep0,
    'rep1': rep1,
    'op': op,
    'exclusion': exclusion,
    'tilde': tilde,
    'endswith': endswith,
    'question': question,
    'act': act,
}

