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
class ctx_register(register):
    ctx:register

@dataclass
class i_exception(ctx_register):
    exc_type:register
    exc_val:register
    exc_traceback:register

@dataclass
class i_return(ctx_register):
    val:register

@dataclass
class i_yield(ctx_register):
    val:register
    return_addr:register
    yields:bool=False

@dataclass
class i_loop(ctx_register):
    break_addr:register

class context(register):

    def __init__(self, t:context_tracing):
        super().__init__('ctx-addr')
        self.tracing = t
        self.stack_addr = self.reg('stk-addr')
        self.except_addr = i_exception('exc-addr', self,
            self.reg('exc-type'),
            self.reg('exc-val'),
            self.reg('exc-trcbk'))

        self.return_addr:'i_return|None' = None
        self.yield_addr:'i_yield|None' = None
        self.continue_addr:'i_loop|None' = None

    def return_to(self):
        self.return_addr = i_return('ret-addr', self,
            self.reg('ret-val'))
        return self

    def yield_to(self):
        self.yield_addr = i_yield('yld-addr', self,
            self.reg('yld-val'),
            self.reg('yld-ret-addr'))
        return self

    def reg(self, msg):
        return ctx_register(msg, self)

class instruction:

    def elements(self) -> tuple:
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
            e = tuple(self.getstr(s).ljust(20) for s in i.elements())
            i = self.getstr(i).ljust(5)
            print(i, *e, sep='')

    def getinsts(self):
        for n in self.labels.list:
            if n.prv is not None: continue
            while n: yield n.inst; n = n.nxt

    def getstr(self, s):
        if isinstance(s, instruction):
            return self.label(s)
        elif isinstance(s, register):
            return self.reg(s)
        elif isinstance(s, str):
            return s
        elif isinstance(s, tuple):
            return ' '.join(self.getstr(i) for i in s)
        elif s is True:
            return 'True'
        elif s is False:
            return 'False'
        elif s is None:
            return 'None'
        raise NotImplementedError(type(s))

    def label(self, i:instruction):
        n = self.i_nodes[id(i)]
        # self.labels[id(n)] = n
        idx = self.labels.map.get(id(n))
        if idx is None: return '  '
        return '@' + str(idx)

    def reg(self, r:register):
        self.registers[id(r)] = r
        idx = self.registers.map[id(r)]
        return f'{idx}({r.msg})'

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
        self_n = super().newnode(c)
        c.stack.append(self)
        return self_n

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
class peek_stack_i(nxt_instruction):
    target:register
    stack_addr:register

    def elements(self):
        return 'stk-peek', self.stack_addr, self.target

@dataclass
class assign_i(nxt_instruction):
    target_ref:register
    arg:register

    def elements(self):
        return 'assign', self.target_ref, self.arg

@dataclass
class copy_i(nxt_instruction):
    target:register
    arg:register

    def elements(self):
        return 'copy', self.target, self.arg

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
class prog_i(nxt_instruction):

    def elements(self):
        return 'program',

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

    def newnode(self, c: compiler) -> i_node:
        self_n = c.setnode(self, i_node(self))
        inst_n = c.getnode(self.inst)
        c.addlabel(inst_n)
        c.stack.append(self)
        return self_n

@dataclass
class jump_reg_i(instruction):
    jump_addr:register

    def elements(self):
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
            invert_target = register('branch-invert-test', None)
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

@dataclass
class call_i(nxt_instruction):
    target:register
    func:register
    args:register

    def elements(self):
        return 'call', self.target, self.func, self.args

@dataclass
class iter_i(nxt_instruction):
    target:register
    iterable:register

    def elements(self):
        return 'iter', self.target, self.iterable

@dataclass
class next_i(nxt_instruction):
    target:register
    iterator:register
    return_addr:i_return

    def elements(self):
        return 'next', self.target, self.iterator, self.return_addr

@dataclass
class generator_i(nxt_instruction):
    target:register
    jump:instruction
    gen_ctx:context

    def elements(self):
        return 'generator', self.target, self.jump, self.gen_ctx

    def newnode(self, c: compiler) -> i_node:
        self_n = c.setnode(self, i_node(self))
        jump_n = c.getnode(self.jump)
        c.addlabel(jump_n)
        c.stack.append(self)
        return self_n

############################################################
# Literals
@dataclass
class int_lit_i(nxt_instruction):
    target:register
    name:str

    def elements(self):
        return 'int-l', self.target, self.name

@dataclass
class bool_lit_i(nxt_instruction):
    target:register
    val:'bool|None'

    def elements(self):
        return 'bool-l', self.target, self.val


@dataclass
class list_i(nxt_instruction):
    target:register
    args:tuple[register, ...]

    def elements(self):
        return 'list', self.target, *self.args

@dataclass
class tuple_i(nxt_instruction):
    target:register
    args:tuple[register, ...]

    def elements(self):
        return 'tuple', self.target, *self.args

############################################################
# Values

@dataclass
class hint_i(nxt_instruction):
    target_ref:register
    info:register

    def elements(self):
        return 'hint', self.target_ref, self.info

@dataclass
class idf_i(nxt_instruction):
    target:register
    name:str

    def elements(self):
        return 'idf', self.target, self.name

@dataclass
class idf_target_i(nxt_instruction):
    target_addr:register
    name:str

    def elements(self):
        return 'idf-t', self.target_addr, self.name

@dataclass
class subscript_i(nxt_instruction):
    target:register
    prim:register
    arg:register

    def elements(self):
        return 'subscript', self.target, self.prim, self.arg

@dataclass
class subscript_target_i(nxt_instruction):
    target_addr:register
    prim:register
    arg:register

    def elements(self):
        return 'subscript-t', self.target_addr, self.prim, self.arg

@dataclass
class attribute_ref_i(nxt_instruction):
    target:register
    prim:register
    attrib:str

    def elements(self):
        return 'attrib', self.target, self.prim, self.attrib


############################################################
# Operators

@dataclass
class unary_op_i(nxt_instruction):
    op:str
    target:register
    arg:register

    def elements(self):
        return self.op, self.target, self.arg

@dataclass
class binary_op_i(nxt_instruction):
    op:str
    target:register
    arga:register
    argb:register

    def elements(self):
        return self.op, self.target, self.arga, self.argb
