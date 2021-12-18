# cycompiler.py
import cyassembler as assy

class context_paths:

    def set_stack(self, *joins:'context_paths'):
        return context_paths(), context()

    def reset_stack(self):
        return context_paths()

    def join(self, *joins:'context_paths'):
        return context_paths()

    def split_nxt(self, *joins:'context_paths'):
        return context_paths(), context()

class context:

    def set_stack(self, *joins:context_paths):
        return context_paths(), context()

    def join_nxt(self, *joins:context_paths):
        return context_paths()

    def push_reg(self, *joins:context_paths):
        return context_paths(), context()

    def reg_peeks(self, count:int, *joins:context_paths):
        return context_paths(), context()

    def reg_pops(self, count:int, *joins:context_paths):
        return context_paths(), context()

    def del_pops(self, count:int, *joins:context_paths):
        return context_paths(), context()

    def inst(self, i:str, op:str, *joins:context_paths):
        return context_paths(), context()

    def path_inst(self, op:str, paths:context_paths, *joins:context_paths):
        return context_paths()

    def setrange(self, s:int, e:int):
        return context()

    def branch(self, *joins:context_paths):
        return context_paths(), context(), context()
