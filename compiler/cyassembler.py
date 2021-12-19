# cyassembler.py
from cycompiler import *

class a_node:

    def setid(self, i:int):
        self.id = f'@{i}'
        for n in self.nexts.values():
            n.prevs[i] = self
        return self

    def __init__(self, op:str, info:str, **nexts:'a_node'):
        self.id = None
        self.op = op
        self.info = info
        self.prevs:dict[int, a_node] = {}
        self.nexts = nexts

    def __str__(self):
        f = f'{self.id} "{self.op}", "{self.info}"' + \
            ','.join(f' {n}:{i.id}' for n,i in self.nexts.items()) + \
            f" ({', '.join(i.id for i in self.prevs.values())})"
        return f

class assembler:
    
    def __init__(self, f:base_context) -> None:
        self.insts:dict[int, a_node] = {}
        self.nodes:dict[int, a_node] = {}
        self.stack:list[base_context] = [f]

        def gen_nodes():
            while self.stack:
                c = self.stack.pop()
                yield self.proc(c)
            for n in self.nodes.values():
                if n.id is None:
                    yield n
        
        def gen_labels():
            for i,l in enumerate(gen_nodes()):
                yield l.setid(i)

        for l in tuple(gen_labels()):
            print(str(l))

    def getnode(self, c:base_context, **nexts:a_node) -> a_node:
        node = self.insts.get(id(c))
        if node is None:
            op_info = c.op_info()
            if (isinstance(c, context) and
                (op_info == ('join', 'no-op')
                or op_info[0] == 'range'
                or op_info[0] == 'pass')):
                if c._next is None:
                    node = a_node(*op_info, **nexts)
                    self.nodes[id(node)] = node
                else:
                    node = self.getnode(c._next)
            else:
                node = a_node(*op_info, **nexts)
                self.nodes[id(node)] = node
                self.stack.append(c)
            self.insts[id(c)] = node
        else:
            for k in set(node.nexts.keys()).intersection(nexts.keys()):
                assert node.nexts[k] == nexts[k]
            node.nexts.update(nexts)
        return node

    def proc(self, c:base_context):
        if isinstance(c, context_paths):
            nodes = dict((n,self.getnode(ctx)) for n,ctx in c._ctxs.items())
            return self.getnode(c, **nodes)
        elif isinstance(c, context):
            if c._next is None:
                x_node = a_node('exit', 'error')
                self.nodes[id(x_node)] = x_node
                ns = dict(n=x_node)
            elif isinstance(c._next, context_paths):
                ns = dict((k,self.getnode(c)) for k,c in c._next._ctxs.items())
            else:
                ns = dict(n=self.getnode(c._next))

            if isinstance(c, context_frame):
                return self.getnode(c, **ns,
                    s=self.getnode(c._ctx_start),
                    x=self.getnode(c._exit_paths))
            else:
                return self.getnode(c, **ns)
        raise NotImplementedError(c.__class__.__name__)
