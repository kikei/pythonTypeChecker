
class ty:
    """Base meta type. This is normally abstract."""
    def __init__(self):
        self.__type__ = "*"
    def __eq__(a,b):
        return True

def typeFunction(f):
    """Returns function type when f's type is explicitly defined.
    Otherwise returns unknown function type, so type check is disabled."""
    def typeAnn(ann):
        arg = []
        res = fnTyUnknown()
        
        for (k,v) in ann.items():
            if isinstance(v, fnTyUnknown):
                raise TypeError
            if k == 'return':
                res = v
            else:
                arg.append((k, v))
                
        if isinstance(res, fnTyUnknown):
            raise TypeError
        return (arg, res)

    try:
        (a, r) = typeAnn(f.ann)
    except TypeError as e:
        return fnTyUnknown()
    
    return fnTy(f.args, dict(a), r)

def typing(a):
    """Judge value a's type."""
    
    if isinstance(a, tuple):
        return tuple(typing(b) for b in a)
    elif isinstance(a, list):
        return [typing(b) for b in a]
    elif isinstance(a, set):
        return set(typing(b) for b in a)
    elif isinstance(a, dict):
        return dict((n,typing(v)) for (n,v) in a.items())
    elif isinstance(a, tfunction):
        return typeFunction(a)
    else:
        return type(a)

def typeToStr(t):
    """Build string fron type."""
    def seq(b, s, e):
        return b + ", ".join(typeToStr(tt) for tt in t) + e
    
    if isinstance(t, tuple):
        return seq("(",t,")")
    elif isinstance(t, list):
        return seq("[",t,"]")
    elif isinstance(t, set):
        return seq("set(",t,")")
    elif isinstance(t, dict):
        return "{" + ", ".join("%s:%s" % (str(k), typeToStr(v))
                               for (k,v) in t.items()) + "}"
    elif isinstance(t, ty):
        return t.__type__
    else:
        return t.__name__

# types
class dictTy(ty):
    """Dict type which may be abbreviated."""
    def __init__(self, *args, **kws):
        self.dict = dict(*args, **kws)
        self.__type__ = "{" + \
                        ", ".join("%s:%s" % (str(k), typeToStr(v))
                                  for (k,v) in self.dict.items()) + \
                        ", ...}"
    def __eq__(a,b):
        for (k,v) in a.dict.items():
            if not k in b or not b.get(k) == v:
                return False
        return True

class listTy(ty):
    """List type whose all element have same type."""
    def __init__(self, ty):
        self.ty = ty
        self.__type__ = "[%s, ...]" % typeToStr(ty)
    def __eq__(a,b):
        return len(b) == 0 or len(b) == b.count(a.ty)

class fnTy(ty):
    """Lambda type"""
    def __init__(self, args, ann, res):
        def at(a): 
            if a in ann:
                return ann.get(a)
            else:
                return ty()
            
        self.args = args
        self.ann = ann
        self.res = res
        self.__type__ = "((%s) -> %s)" % \
                        (', '.join(typeToStr(at(a)) for a in args),
                         typeToStr(res))
    def __eq__(a, b):
        if isinstance(b, fnTy):
            return [a.ann.get(k) for k in a.args] == \
                   [b.ann.get(k) for k in b.args] and \
                   a.res == b.res


class fnTyUnknown(ty):
    """Unknown lambda type"""
    def __init__(self):
        self.__type__ = "(? -> ?)"

# objects
class tfunction:
    """Object of function typed by fun. Remember arg specs."""
    def __init__(self, func):
        self.func = func
        
        args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = \
            inspect.getfullargspec(func)
        self.args = args
        self.varargs = varargs
        self.varkw = varkw
        self.defaults = defaults
        self.kwonlyargs = kwonlyargs
        self.kwdefaults = kwdefaults
        self.ann = ann

    def __call__(self, *a, **k):
        # check arguments
        nv = zip(self.args, a)
        for (n,v) in nv:
            aty = self.ann.get(n)
            vty = typing(v)
            if n in self.ann and not aty == vty:
                raise TypeError(
                    ("Type mismatch of function arguments.\n"+
                     "typed: %s\nvalue: %s")
                     % (typeToStr(aty), typeToStr(vty)))
        # execution
        r = self.func(*a)
        # check results
        aty = self.ann.get('return')
        vty = typing(r)
        if 'return' in self.ann and not aty == vty:
            raise TypeError(("Type mismatch of function result.\n"+
                             "typed: %s\nvalue: %s")
                             % (typeToStr(aty), typeToStr(vty)))
        return r


import functools
import inspect

# decorator
def fun(func):
    """Type checker"""
    args, varargs, varkw, defaults, kwonlyargs, kwdefaults, ann = \
        inspect.getfullargspec(func)
    # print(":::%s:::\n" % func.__name__)
    # print("arg: %s\n\n" % str(inspect.getfullargspec(func)))

    return tfunction(func)

# utilities
class fn:
    """Lambda type constructor for type annotations."""
    def __init__(self, *fr):
        self.fr = fr
    def __rshift__(f, to):
        args = ["arg%d" % i for i in range(0, len(f.fr))]
        ann  = [(args[i], f.fr[i]) for i in range(0, len(f.fr))]
        return fnTy(args, dict(ann), to)

@tc.fun
def printType(x):
    """Print type"""
    print(typeToStr(typing(x)))

