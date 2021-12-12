# cycompiler.py
from dataclasses import dataclass, astuple
from typing import Callable, Generic, Iterable, NoReturn, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class listmap(Generic[K,V]):
    def __init__(self):
        self.map:dict[K,int] = {}
        self.list:list[V] = []

    def __getitem__(self, k:K):
        idx = self.map.get(k)
        if idx is None: return idx
        return self.list[idx]

    def __setitem__(self, k:K, v:V):
        if k in self.map:
            self.list[self.map[k]] = v
            return

        self.map[k] = len(self.list)
        self.list.append(v)

class context_tracing:
    def error(self, msg:str) -> NoReturn:
        raise NotImplementedError(msg)

    def update(self, startidx:int, stopidx:int) -> tuple[int,int]:
        raise NotImplemented(startidx, stopidx)

@dataclass
class i_node:
    inst:'base_instruction'
    checked:bool=False
    prv:'i_node|None'=None
    nxt:'i_node|None'=None
    undefined:'bool'=False

@dataclass
class register:
    msg:str

@dataclass
class base_instruction:
    nxt:'base_instruction|None'

    def elements(self) -> 'tuple[base_instruction|register|str|None, ...]':
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: 'compiler') -> i_node:
        raise NotImplementedError(self.__class__.__name__)

    def checknxt(self, c: 'compiler', n: i_node):
        raise NotImplementedError(self.__class__.__name__)

@dataclass
class context:
    tracing:context_tracing
    stack_addr:register
    raise_to:'raise_i'

    return_to:base_instruction=None
    yield_to:base_instruction=None
    yields:bool=False

    continue_to:base_instruction=None
    break_to:base_instruction=None

class compiler:

    def __init__(self, inst:base_instruction):
        self.i_nodes:dict[int,i_node] = {}
        self.stack:list[base_instruction] = []

        self.labels = listmap[int,i_node]()
        self.registers = listmap[int,register]()

        root = self.getnode(inst)
        self.addlabel(root)
        while self.stack and (i := self.stack.pop()):
            if not (n := self.i_nodes[id(i)]).checked:
                n.checked = True
                i.checknxt(self, n)

        for i in self.getinsts():
            e = tuple(self.getstr(s).ljust(12) for s in i.elements())
            i = self.getstr(i).ljust(5)
            print(i, *e, sep='')

    def getinsts(self):
        for n in self.labels.list:
            if n.prv is not None: continue
            while n: yield n.inst; n = n.nxt

    def getstr(self, s:'base_instruction|register|str|None'):
        if isinstance(s, base_instruction):
            return self.label(s)
        elif isinstance(s, register):
            return self.reg(s)
        elif s is None:
            return 'None'
        return s

    def label(self, i:base_instruction):
        n = self.i_nodes[id(i)]
        # self.labels[id(n)] = n
        idx = self.labels.map.get(id(n))
        if idx is None: return '  '
        return '@' + str(idx)

    def reg(self, r:register):
        self.registers[id(r)] = r
        idx = self.registers.map[id(r)]
        return '$' + str(idx)

    def addlabel(self, n:i_node):
        self.labels[id(n)] = n

    def getnode(self, i:base_instruction):
        n = self.i_nodes.get(id(i)) or i.newnode(self)
        assert not n.undefined
        return n

    def setnode(self, i:base_instruction, n:i_node):
        self.i_nodes[id(i)] = n
        return n

@dataclass
class instruction(base_instruction):
    nxt:base_instruction

    def elements(self):
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: 'compiler') -> i_node:
        c.stack_frame.append(self)
        return c.setnode(self, i_node(self))

    def checknxt(self, c: 'compiler', n: i_node):
        n.nxt = c.getnode(self.nxt)
        if n.nxt.prv is not None:
            c.addlabel(n.nxt)
            self.nxt = j = jump_i(None, n.nxt.inst)
            n.nxt = c.setnode(j, i_node(j))
        n.nxt.prv = n
        return n

############################################################
# data flow

@dataclass
class new_stack_i(instruction):
    target:register

    def elements(self):
        return 'stk-new', self.target

@dataclass
class push_stack_i(instruction):
    stack_addr:register
    arg:register

    def elements(self):
        return 'stk-push', self.stack_addr, self.arg

@dataclass
class pop_stack_i(instruction):
    target:register
    stack_addr:register

    def elements(self):
        return 'stk-pop', self.stack_addr, self.target

@dataclass
class assign_i(instruction):
    target:register
    arg:register

    def elements(self):
        return 'assign', self.target, self.arg

############################################################
# instruction flow
@dataclass
class hang_i(base_instruction):
    '''
    loop indefinitely
    '''
    nxt:None=None

    def elements(self):
        return 'hang',

@dataclass
class exit_i(base_instruction):
    nxt:None
    code:register

    def elements(self):
        return 'exit', self.code

    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, i_node(self))

@dataclass
class store_inst_i(instruction):
    target:register
    inst:base_instruction

    def elements(self):
        return 'store-i', self.target, self.inst

@dataclass
class jump_reg_i(base_instruction):
    nxt:None
    jump:register

    def elements(self) -> 'tuple[base_instruction|register|str|None, ...]':
        return 'jump-r', self.jump
    
    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, i_node(self))

@dataclass
class jump_i(base_instruction):
    '''
    go to jump
    '''
    nxt:None
    jump:base_instruction

    def elements(self):
        return 'jump', self.jump

    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, c.getnode(self.jump))

@dataclass
class pass_i(instruction):
    def elements(self):
        return 'pass',

    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, c.getnode(self.nxt))

@dataclass
class comment_i(pass_i):
    lines:tuple[str, ...]

    def elements(self):
        return '#', *self.lines

@dataclass
class invert_i(instruction):
    target:register
    arg:register

    def elements(self):
        return 'invert', self.target, self.arg

@dataclass
class branch_i(instruction):
    '''
    go to nxt if reg is true;
    go to branch if reg is false
    '''

    branch:base_instruction
    test:register

    def elements(self):
        return 'if', self.branch, self.test

    def newnode(self, c: 'compiler') -> i_node:
        self_n = c.setnode(self, i_node(self, undefined=True))
        branch_n = c.getnode(self.branch)
        nxt_n = c.getnode(self.nxt)

        if isinstance(i := branch_n.inst, branch_i) and i.test == self.test:
            self.branch = i.branch
            branch_n = c.getnode(i)

        if isinstance(i := nxt_n.inst, branch_i) and i.test == self.test:
            self.nxt = i.nxt
            nxt_n = c.getnode(i)

        if branch_n == nxt_n:
            return c.setnode(self, branch_n)

        if branch_n.prv is None and nxt_n.prv is not None:
            invert_target = register('branch-invert-test')
            br = branch_i(branch_n.inst, nxt_n.inst, invert_target)
            i = invert_i(br, invert_target, self.test)
            return c.setnode(self, c.getnode(i))

        c.addlabel(branch_n)

        self_n.undefined = False
        c.stack_frame.append(self)
        return self_n


@dataclass
class raise_i(base_instruction):
    nxt:None
    exc_addr:register
    exc_type:register
    exc_value:register
    exc_traceback:register

@dataclass
class except_i(instruction):
    exc_type:register
    exc_value:register
    exc_traceback:register

    def elements(self):
        return 'except', self.exc_type, self.exc_value, self.exc_traceback

@dataclass
class args_i(instruction):
    target:register
    args:tuple[register, ...]

@dataclass
class call_i(instruction):
    return_val:register
    func:register
    args:register
    stack_addr:register
    raise_to:raise_i

############################################################
# Literals
@dataclass
class int_lit_i(instruction):
    target:register
    name:str

    def elements(self):
        return 'int-l', self.name

############################################################
# Targets

@dataclass
class idf_target_i(instruction):
    target:register
    name:str

    def elements(self):
        return 'idf-t', self.target, self.name
