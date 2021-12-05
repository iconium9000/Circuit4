# cycompiler.py
from dataclasses import dataclass, astuple
from typing import Callable, Generic, Iterable, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class listmap(Generic[K,V]):
    def __init__(self):
        self.map:dict[K,int] = {}
        self.list:list[V] = []

    def __contains__(self, k:K):
        return k in self.map

    def get(self, k:K):
        if k in self.map:
            return self.list[self.map[k]]

    def add(self, k:K, v:V):
        if k in self.map:
            self.list[self.map[k]] = v
            return

        self.map[k] = len(self.list)
        self.list.append(v)
    
    def next(self, idx:int):
        if idx < len(self.list):
            return self.list[idx]

def reverse(t:tuple[V, ...]): return (t[i] for i in range(len(t)-1, -1, -1))

@dataclass
class control:
    raise_to:'instruction'
    break_to:'instruction|None'=None
    continue_to:'instruction|None'=None
    return_to:'instruction|None'=None
    yield_to:'instruction|None'=None
    yields:bool=False

@dataclass
class register: pass

@dataclass
class base_instruction:
    next:'base_instruction|None'

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'base',

@dataclass
class instruction(base_instruction):
    next:base_instruction

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'inst'

@dataclass
class exit_i(base_instruction):
    next:None
    code:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'exit', self.code

@dataclass
class jump_i(base_instruction):
    '''
    go to jump
    '''
    next:None
    jump:instruction

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'jump', self.jump

class compile:

    def __init__(self, itc:Callable[[control, instruction, register], instruction]):
        self.insts = listmap[int,base_instruction]()
        self.labels = listmap[int,str]()
        self.regs = listmap[int,register]()

        exc_value = register()
        exc_type = register()
        exc_traceback = register()

        exit_to = exit_i(None, exc_value)
        raise_to = except_i(exit_to, exit_to, exc_type, exc_value, exc_traceback)
        ctrl = control(raise_to)
        inst = itc(ctrl, pass_i(exit_to), exc_value)

        self.max_label_len = 0
        self.catalog(inst)
        self.empty_label = ' ' * self.max_label_len

    def label(self, i:base_instruction):
        return self.labels.get(id(i)) or self.empty_label

    def reg(self, r:register):
        if id(r) not in self.regs:
            self.regs.add(id(r), r)
        return '$' + str(self.regs.map[id(r)])

    def getstr(self, e:'base_instruction|register|str'):
        if isinstance(e, base_instruction): return self.label(e)
        if isinstance(e, register): return self.reg(e)
        return e

    def inststr(self, i:Iterable[str]):
        return ' '.join(self.getstr(e).ljust(7) for e in i)

    def __str__(self):
        s = 'Compiled output:\n'

        def getlabelstr(label:str):
            if label: return label.ljust(self.max_label_len)
            else: return self.empty_label

        for inst in self.insts.list:
            label = self.labels.get(id(inst))
            labelstr = getlabelstr(label)
            inststr = self.inststr(inst.elements())
            s += labelstr + ' ' + inststr + '\n'

        return s

    def newlabel(self):
        idx = len(self.labels.list)
        label = '@' + str(idx)
        label_len = len(label)
        if self.max_label_len < label_len:
            self.max_label_len = label_len
        return label

    def checkinst(self, inst:base_instruction):
        if id(inst) in self.labels:
            return False
        elif id(inst) in self.insts:
            self.labels.add(id(inst), self.newlabel())
            return False
        self.insts.add(id(inst), inst)
        if id(inst.next) in self.insts.map:
            self.checkinst(inst.next)
            inst.next = jump_i(None, inst.next)
            self.checkinst(inst.next)
        return True

    def catalog(self, inst:base_instruction) -> None:
        while inst and self.checkinst(inst):
            if isinstance(binst := inst, branch_i):
                self.catalog(binst.next)
                self.catalog(binst.branch)
                self.checkinst(binst.branch)
                return
            inst = inst.next

@dataclass
class pass_i(instruction):
    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'pass',

@dataclass
class branch_i(instruction):
    '''
    go to next if reg is true;
    go to branch if reg is false
    '''

    branch:instruction
    test:register

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return 'branch', self.branch, self.test

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
