
def decorator(f):
    def wrapper(*args):
        print('wrapper', *args)
        return f(*args)
    return wrapper

@decorator
def foo(a,b,c):
    print(a,b,c)



