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

    def assign_context(self, i:'instruction') -> None:
        raise NotImplemented(id(i))

@dataclass
class i_node:
    inst:'instruction'
    checked:bool=False
    prv:'i_node|None'=None
    nxt:'i_node|None'=None
    undefined:'bool'=False

@dataclass
class register:
    msg:str

@dataclass
class i_exception(register):
    exc_type:register
    exc_val:register
    exc_traceback:register

@dataclass
class i_return(register):
    ret_val:register

@dataclass
class context(register):
    tracing:context_tracing
    stack_addr:register
    except_addr:i_exception
    return_addr:'i_return|None'=None
    yield_addr:'i_return|None'=None
    yields:bool=False

    continue_addr:'register|None'=None
    break_addr:'register|None'=None

class instruction:

    def elements(self) -> 'tuple[instruction|register|str|None, ...]':
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, i_node(self))

class compiler:

    def __init__(self, inst:instruction):
        self.i_nodes:dict[int,i_node] = {}
        self.stack:list[nxt_instruction] = []

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

    def getstr(self, s:'instruction|register|str|None'):
        if isinstance(s, instruction):
            return self.label(s)
        elif isinstance(s, register):
            return self.reg(s)
        elif s is None:
            return 'None'
        return s

    def label(self, i:instruction):
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

    def getnode(self, i:instruction):
        n = self.i_nodes.get(id(i)) or i.newnode(self)
        assert not n.undefined
        return n

    def setnode(self, i:instruction, n:i_node):
        self.i_nodes[id(i)] = n
        return n

@dataclass
class nxt_instruction(instruction):
    ctx:context
    nxt:instruction

    def elements(self):
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: compiler) -> i_node:
        c.stack.append(self)
        return c.setnode(self, i_node(self))

    def checknxt(self, c: compiler, n: i_node):
        n.nxt = c.getnode(self.nxt)
        if n.nxt.prv is not None:
            c.addlabel(n.nxt)
            self.nxt = j = jump_i(n.nxt.inst)
            n.nxt = c.setnode(j, i_node(j))
        n.nxt.prv = n
        return n

############################################################
# data flow

@dataclass
class init_stack_i(nxt_instruction):
    target:register

    def elements(self):
        return 'stk-new', self.target

@dataclass
class push_stack_i(nxt_instruction):
    stack_addr:register
    arg:register

    def elements(self):
        return 'stk-push', self.stack_addr, self.arg

@dataclass
class pop_stack_i(nxt_instruction):
    target:register
    stack_addr:register

    def elements(self):
        return 'stk-pop', self.stack_addr, self.target

@dataclass
class assign_i(nxt_instruction):
    target:register
    arg:register

    def elements(self):
        return 'assign', self.target, self.arg

############################################################
# instruction flow
@dataclass
class hang_i(instruction):
    '''
    loop indefinitely
    '''

    def elements(self):
        return 'hang',

@dataclass
class exit_i(instruction):
    code:register

    def elements(self):
        return 'exit', self.code

@dataclass
class store_inst_i(nxt_instruction):
    target:register
    inst:instruction

    def elements(self):
        return 'store-i', self.target, self.inst

@dataclass
class jump_reg_i(instruction):
    jump_addr:register

    def elements(self) -> 'tuple[instruction|register|str|None, ...]':
        return 'jump-r', self.jump_addr

@dataclass
class jump_i(instruction):
    '''
    go to jump
    '''
    jump:instruction

    def elements(self):
        return 'jump', self.jump

    def newnode(self, c: compiler) -> i_node:
        return c.setnode(self, c.getnode(self.jump))

@dataclass
class pass_i(nxt_instruction):
    def elements(self):
        return 'pass',

    def newnode(self, c: compiler) -> i_node:
        return c.setnode(self, c.getnode(self.nxt))

@dataclass
class invert_i(nxt_instruction):
    target:register
    arg:register

    def elements(self):
        return 'invert', self.target, self.arg

@dataclass
class branch_i(nxt_instruction):
    '''
    go to nxt if reg is true;
    go to branch if reg is false
    '''

    branch:instruction
    test:register

    def elements(self):
        return 'if', self.branch, self.test

    def newnode(self, c: compiler) -> i_node:
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
            br = branch_i(self.ctx, branch_n.inst, nxt_n.inst, invert_target)
            i = invert_i(self.ctx, br, invert_target, self.test)
            return c.setnode(self, c.getnode(i))

        c.addlabel(branch_n)

        self_n.undefined = False
        c.stack.append(self)
        return self_n

@dataclass
class args_i(nxt_instruction):
    target:register
    args:tuple[register, ...]

    def elements(self):
        return 'args', self.target, *self.args

############################################################
# Literals
@dataclass
class int_lit_i(nxt_instruction):
    target:register
    name:str

    def elements(self):
        return 'int-l', self.name

@dataclass
class bool_lit_i(nxt_instruction):
    target:register
    val:'bool|None'

    def elements(self):
        return 'bool-l', self.target, self.val

############################################################
# Values

@dataclass
class idf_i(nxt_instruction):
    target:register
    name:str

    def elements(self):
        return 'idf', self.target, self.name

@dataclass
class idf_target_i(nxt_instruction):
    target:register
    name:str

    def elements(self):
        return 'idf-t', self.target, self.name
