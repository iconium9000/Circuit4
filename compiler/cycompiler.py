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

    def __init__(self, manip:control_manip):
        self.insts = listmap[int,base_instruction]()
        self.labels = listmap[int,str]()
        self.regs = listmap[int,register]()

        exc_value = register()
        exc_type = register()
        exc_traceback = register()

        exit_to = exit_i(None, exc_value)
        raise_to = except_i(exit_to, exit_to, exc_type, exc_value, exc_traceback)
        ctrl = control(manip, 0, 0, raise_to)
        inst = manip.itc(ctrl, pass_i(exit_to), exc_value)

        self.max_label_len = 0
        self.catalog(inst)
        self.empty_label = ' ' * self.max_label_len

    def label(self, i:base_instruction):
        idx = self.insts.map[id(i)]
        return self.labels[idx] or self.empty_label

    def reg(self, r:register):
        if id(r) not in self.regs.map:
            self.regs[id(r)] = r
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

        for idx,inst in enumerate(self.insts.list):
            label = self.labels[idx]
            labelstr = getlabelstr(label)
            inststr = self.inststr(inst.elements())
            s += labelstr + ' ' + inststr + '\n'
        return s

    def newlabel(self, instidx:int):
        if label := self.labels[instidx]: return
        idx = len(self.labels.list)
        label = '@' + str(idx)
        label_len = len(label)
        if self.max_label_len < label_len:
            self.max_label_len = label_len
        self.labels[instidx] = label

    def catalog(self, inst:base_instruction) -> int:
        next = inst
        while next := self.checkinst(next): pass
        return self.insts.map[id(inst)]

    def jump_to(self, inst:base_instruction):
        idx = self.insts.map.get(id(inst))
        if idx is None: return inst
        self.newlabel(idx)
        return jump_i(None, inst)

    def checkinst(self, inst:base_instruction) -> 'base_instruction|None':
        idx = self.insts.map.get(id(inst))
        if idx is not None:
            self.newlabel(idx)
        elif isinstance(inst, jump_i):
            idx = self.insts.map.get(id(inst.jump))
            if idx is None:
                self.insts.map[id(inst)] = self.catalog(inst.jump)
            else: self.newlabel(idx); self.insts[id(inst)] = inst
        elif isinstance(inst, (pass_i, comment_i)):
            inst.next = self.jump_to(inst.next)
            self.insts.map[id(inst)] = self.catalog(inst.next)
        elif isinstance(inst, yield_i):
            self.insts[id(inst)] = inst
            inst.next = self.jump_to(inst.next)
            self.catalog(inst.next)
            self.newlabel(self.catalog(inst.yield_to))
        elif isinstance(inst, branch_i):
            while isinstance(inst.branch, branch_i) and inst.branch.test == inst.test:
                inst.branch = inst.branch.branch
            while isinstance(inst.next, branch_i) and inst.next.test == inst.test:
                inst.next = inst.next.next
            if inst.next == inst.branch:
                jump = self.jump_to(inst.branch)
                self.insts.map[id(inst)] = self.catalog(jump)
            else:
                self.insts[id(inst)] = inst
                inst.next = self.jump_to(inst.next)
                self.catalog(inst.next)
                self.newlabel(self.catalog(inst.branch))
        else:
            self.insts[id(inst)] = inst
            inst.next = self.jump_to(inst.next)
            return inst.next

@dataclass
class comment_i(instruction):
    msg:str

    def elements(self) -> 'tuple[str|base_instruction|register, ...]':
        return '# ' + self.msg,

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
