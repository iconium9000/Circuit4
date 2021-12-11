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
    prev:'i_node|None'=None
    next:'i_node|None'=None
    undefined:'bool'=False

@dataclass
class register:
    msg:str

@dataclass
class base_instruction:
    next:'base_instruction|None'

    def elements(self) -> 'tuple[base_instruction|register|str|None, ...]':
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: 'compiler') -> i_node:
        raise NotImplementedError(self.__class__.__name__)

    def checknext(self, c: 'compiler', n: i_node):
        raise NotImplementedError(self.__class__.__name__)

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
                i.checknext(self, n)

        for i in self.getinsts():
            e = tuple(self.getstr(s).ljust(12) for s in i.elements())
            i = self.getstr(i).ljust(5)
            print(i, *e, sep='')

    def getinsts(self):
        for n in self.labels.list:
            if n.prev is not None: continue
            while n: yield n.inst; n = n.next

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
    next:base_instruction

    def elements(self):
        raise NotImplementedError(self.__class__.__name__)

    def newnode(self, c: 'compiler') -> i_node:
        c.stack_frame.append(self)
        return c.setnode(self, i_node(self))

    def checknext(self, c: 'compiler', n: i_node):
        n.next = c.getnode(self.next)
        if n.next.prev is not None:
            c.addlabel(n.next)
            self.next = j = jump_i(None, n.next.inst)
            n.next = c.setnode(j, i_node(j))
        n.next.prev = n
        return n

@dataclass
class hang_i(base_instruction):
    '''
    loop indefinitely
    '''
    next:None=None

    def elements(self):
        return 'hang',

@dataclass
class exit_i(base_instruction):
    next:None
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
    next:None
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
    next:None
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
        return c.setnode(self, c.getnode(self.next))

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
    go to next if reg is true;
    go to branch if reg is false
    '''

    branch:base_instruction
    test:register

    def elements(self):
        return 'if', self.branch, self.test

    def newnode(self, c: 'compiler') -> i_node:
        self_n = c.setnode(self, i_node(self, undefined=True))
        branch_n = c.getnode(self.branch)
        next_n = c.getnode(self.next)

        if isinstance(i := branch_n.inst, branch_i) and i.test == self.test:
            self.branch = i.branch
            branch_n = c.getnode(i)

        if isinstance(i := next_n.inst, branch_i) and i.test == self.test:
            self.next = i.next
            next_n = c.getnode(i)

        if branch_n == next_n:
            return c.setnode(self, branch_n)

        if branch_n.prev is None and next_n.prev is not None:
            invert_target = register('branch-invert-test')
            br = branch_i(branch_n.inst, next_n.inst, invert_target)
            i = invert_i(br, invert_target, self.test)
            return c.setnode(self, c.getnode(i))

        c.addlabel(branch_n)

        self_n.undefined = False
        c.stack_frame.append(self)
        return self_n
