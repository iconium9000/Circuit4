# cycompiler.py
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

K = TypeVar('K')
V = TypeVar('V')

class listmap(Generic[K,V]):
    def __init__(self):
        self.map:dict[K,int] = {}
        self.list:list[V] = []

    def __contains__(self, k:K):
        return k in self.map

    def get(self, k:K):
        return self.map.get(k)

    def add(self, k:K, v:V):
        if k in self.map:
            self.list[self.map[k]] = v
            return

        self.map[k] = len(self.list)
        self.list.append(v)

    def __iter__(self):
        return enumerate(self.list)

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
class instruction:
    next:'instruction|exit_i'

@dataclass
class exit_i:
    code:register
    next:None=None

@dataclass
class pass_i(instruction): pass

@dataclass
class branch_i(instruction):
    '''
    go to next if reg is true;
    go to branch if reg is false
    '''

    branch:instruction
    test:register

@dataclass
class except_i(instruction):
    raise_to:'instruction|exit_i'
    exc_type:register
    exc_value:register
    exc_traceback:register

@dataclass
class assign_i(instruction):
    target:register
    arg:register

@dataclass
class await_i(instruction):
    target:register
    arg:register

@dataclass
class binary_op_i(instruction):
    op:str
    target:register
    arga:register
    argb:register

@dataclass
class compare_i(binary_op_i): pass

@dataclass
class unary_op_i(instruction):
    op:str
    target:register
    arg:register

@dataclass
class number_i(instruction):
    target:register
    num:str

@dataclass
class identifier_i(instruction):
    target:register
    idf:str

@dataclass
class string_i(instruction):
    target:register
    string:str

@dataclass
class strings_i(instruction):
    target:register
    strings:tuple[register]

@dataclass
class bool_i(instruction):
    target:register
    val:'bool|None'

@dataclass
class ellipsis_i(instruction):
    target:register

class compile:

    def __init__(self, itc:Callable[[control, instruction, register], instruction]):
        self.insts = listmap[int,instruction]()
        self.labels = listmap[int,instruction]()
        self.regs = listmap[int,register]()

        exc_value = register()
        exc_type = register()
        exc_traceback = register()

        exit_to = exit_i(exc_value)
        raise_to = except_i(exit_to, exit_to, exc_type, exc_value, exc_traceback)
        ctrl = control(raise_to)
        inst = itc(ctrl, pass_i(exit_to), exc_value)

        self.catalog(inst)

    def checkinst(self, inst:instruction):
        if id(inst) not in self.labels:
            if id(inst) not in self.insts:
                self.insts.add(id(inst), inst)
                return True
            self.labels.add(id(inst), inst)
        return False

    def catalog(self, inst:'instruction|exit_i') -> None:
        while inst and self.checkinst(inst):
            if isinstance(binst := inst, branch_i):
                return self.catalog(binst.next) or self.catalog(binst.branch)
            inst = inst.next
