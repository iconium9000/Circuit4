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

def reverse(t:tuple[V, ...]): return (t[i] for i in range(len(t)-1, -1, -1))

class control_manip:
    def itc(self, c:'control', i:'instruction', r:'register') -> 'instruction':
        raise NotImplementedError(c, i, r)
    def error(self, msg:str, lnum:int, lidx:int) -> NoReturn:
        raise NotImplementedError(msg, lnum, lidx)
    def getlines(self, slnum:int, slidx:int, elnum:int, elidx) -> Iterable[str]:
        raise NotImplementedError(slnum, slidx, elnum, elidx)

@dataclass
class control:
    manip:control_manip
    lnum:int
    lidx:int
    raise_to:'instruction'
    return_to:'instruction|None'=None
    yields:bool=False
    yield_to:'instruction|None'=None
    break_to:'instruction|None'=None
    continue_to:'instruction|None'=None

    def error(self, msg:str):
        self.manip.error(msg, self.lnum, self.lidx)

@dataclass
class i_node:
    inst:'base_instruction'
    checked:bool=False
    prev:'i_node|None'=None
    next:'i_node|None'=None
    undefined:'bool'=False

@dataclass
class register: pass

@dataclass
class base_instruction:
    next:'base_instruction|None'

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'base',

    def newnode(self, c: 'compiler') -> i_node:
        raise NotImplementedError

    def checknext(self, c: 'compiler', n: i_node):
        raise NotImplementedError

class compiler:

    def __init__(self, manip:control_manip):
        self.i_nodes:dict[int,i_node] = {}
        self.stack:list[base_instruction] = []

        self.labels = listmap[int,i_node]()
        self.registers = listmap[int,register]()

        exc_value = register()
        exc_type = register()
        exc_traceback = register()

        exit_to = exit_i(None, exc_value)
        raise_to = except_i(exit_to, exit_to, exc_type, exc_value, exc_traceback)
        ctrl = control(manip, 0, 0, raise_to)
        inst = manip.itc(ctrl, pass_i(exit_to), exc_value)

        root = self.getnode(inst)
        self.addlabel(root)
        while self.stack and (i := self.stack.pop()):
            if not (n := self.i_nodes[id(i)]).checked:
                n.checked = True
                i.checknext(self, n)

        for i in self.getinsts():
            print(self.getstr(i), *(self.getstr(s) for s in i.elements()))

    def getinsts(self):
        for n in self.labels.list:
            if n.prev is not None: continue
            while n: yield n.inst; n = n.next

    def getstr(self, s:'str|base_instruction|register'):
        if isinstance(s, base_instruction):
            s = self.label(s)
        elif isinstance(s, register):
            s = self.reg(s)
        return s.ljust(7)

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

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'inst'
    
    def newnode(self, c: 'compiler') -> i_node:
        c.stack.append(self)
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

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'hang',

@dataclass
class exit_i(base_instruction):
    next:None
    code:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'exit', self.code

    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, i_node(self))

@dataclass
class jump_i(base_instruction):
    '''
    go to jump
    '''
    next:None
    jump:instruction

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'jump', self.jump
    
    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, c.getnode(self.jump))

@dataclass
class pass_i(instruction):
    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'pass',
    
    def newnode(self, c: 'compiler') -> i_node:
        return c.setnode(self, c.getnode(self.next))

@dataclass
class comment_i(instruction):#(pass_i):
    msg:str

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return '# ' + self.msg,

@dataclass
class branch_i(instruction):
    '''
    go to next if reg is true;
    go to branch if reg is false
    '''

    branch:instruction
    test:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
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
            br = branch_i(branch_n.inst, next_n.inst, reg := register())
            i = unary_op_i(br, 'not', reg, self.test)
            return c.setnode(self, c.getnode(i))

        c.addlabel(branch_n)

        self_n.undefined = False
        c.stack.append(self)
        return self_n

@dataclass
class yield_i(instruction):
    yield_to:instruction
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'yield', self.yield_to, self.arg

@dataclass
class star_i(instruction):
    target:register
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'star', self.target, self.arg

@dataclass
class hint_i(instruction):
    target:register
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'hint', self.target, self.arg

@dataclass
class tuple_i(instruction):
    target:register
    args:tuple[register]

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'tuple', self.target, *self.args

@dataclass
class list_i(tuple_i):
    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'list', self.target, *self.args

@dataclass
class except_i(instruction):
    raise_to:base_instruction
    exc_type:register
    exc_value:register
    exc_traceback:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'except', self.raise_to, self.exc_value, self.exc_traceback

@dataclass
class assign_i(instruction):
    target:register
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'assign', self.target, self.arg

@dataclass
class await_i(instruction):
    target:register
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'await', self.target, self.arg

@dataclass
class binary_op_i(instruction):
    op:str
    target:register
    arga:register
    argb:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return self.op, self.target, self.arga, self.argb

@dataclass
class compare_i(binary_op_i):
    pass

@dataclass
class unary_op_i(instruction):
    op:str
    target:register
    arg:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return self.op, self.target, self.arg

@dataclass
class number_i(instruction):
    target:register
    num:str

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'num', self.target, self.num

@dataclass
class identifier_i(instruction):
    target:register
    idf:str

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'idf', self.target, self.idf

@dataclass
class string_i(instruction):
    target:register
    string:str

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'str', self.target, self.string

@dataclass
class strings_i(instruction):
    target:register
    strings:tuple[register]

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'strs', self.target, *self.strings

@dataclass
class bool_i(instruction):
    target:register
    val:'bool|None'

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return self.val, self.target

@dataclass
class ellipsis_i(instruction):
    target:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return self.target,
