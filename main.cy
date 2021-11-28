if 10 == 10: \
    asdf = 1 # this
            # 456
    asdf += 1
else:
    asdf = -1


print(asdf)
newvar:tuple[
    int,float,
] = 10

def tester():
    i:int = 0x1123
    k:int = 10 / 120

    print(i, k)

    i:list[int] = [1,2,3,4,5]

    def foo(i:int, j:int) -> tuple[int,int]:
        return i,j

    m = 10
    m |= 10

    print(foo(k, i))

"fudge nuggits"