# cycompiler.py

class register:
    pass

class context_paths:

    def exclude_nxt(self, join:'context_paths|None'=None):
        # TODO
        # saves nxt path
        # removes nxt path from path map
        # replaces with empty path
        # ret = nxt
        # if join is not None
        #   joins self paths and join paths
        # returns joined paths, ret
        return context_paths(), context()

    def join_nxt(self, ctx:'context'):
        # TODO
        return self

    def join(self, *paths:'context_paths'):
        # TODO
        # join each ctx in both self and paths
        # return context_paths object with updated values
        return self

class context:

    def __init__(self) -> None:
        pass

    def newframe(self):
        # TODO
        return context()

    def newloop(self):
        # TODO
        return context()

    def setrange(self, s:int, e:int):
        # TODO
        return context()

    def branch(self, join:context_paths):
        # TODO
        # creates two branches
        #   the first assumes the tail value resolves to true
            # the second assumes the tail value resolves to false
        # if the value cannot be cast to a boolean
        #   both of the returned paths
        #   will be marked as exc paths
        return context_paths(), context(), context()

    def clr_tail_val(self):
        # TODO
        # sets the tail value to unbound
        return context()

    def tail_val(self, paths:context_paths):
        # TODO
        return context_paths(), context(), register()

    def program(self, paths:context_paths):
        # TODO
        return context_paths()

    def lookup_idf(self, name:str):
        # TODO
        return context_paths()

    def lookup_ref(self, r:register):
        # TODO
        return context_paths()

    def call(self, func:register, args:register):
        # TODO
        return context_paths()

    def unop(self, op:str, arg:register):
        # TODO
        return context_paths()

    def binop(self, op:str, arga:register, argb:register):
        # TODO
        return context_paths()

    def assign(self, ref:register, arg:register):
        # TODO
        return context_paths()
    
    def hint(self, prim:register, arg:register):
        # TODO
        return context_paths()

    def subscript(self, prim:register, arg:register):
        # TODO
        return context_paths()

    def attrib(self, prim:register, name:str):
        # TODO
        return context_paths()

    def subscript_ref(self, prim:register, arg:register):
        # TODO
        return context_paths()

    def attrib_ref(self, prim:register, name:str):
        # TODO
        return context_paths()

    def next_element(self, iterator:register):
        # TODO
        return context_paths()

    def lit_int(self, v:str):
        # TODO
        # return lit int register
        return context_paths()

    def group(self, group_type:str, *values:register):
        # TODO
        return context_paths()

    def yield_expr(self, r:register):
        # TODO
        return context_paths()

    def loop(self, paths:context_paths):
        # TODO
        return context_paths()

    def generator(self, paths:context_paths):
        # TODO
        return context_paths()

    def iterator(self, iterable:register):
        # TODO
        return context_paths()
