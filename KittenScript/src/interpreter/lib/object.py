# from interpreter.values import Value


class UndefinedType(Value):
    class _undefined(object):
        def __repr__(self):
            return 'undefined'
    
    def __repr__(self):
        return 'undefined'
    
    def get(self):
        return self._undefined()
    

class ClassType(Value):
    class AClass(object):
        def __repr__(self):
            return 'object()'
    
    def __repr__(self):
        s = ''
        for k, v in self.attrs.items():
            s += f'{k}={v}, '
        s = s.strip().strip(',')
        return f'object({s})'
    
    def get(self):
        return self.AClass()
    

functions = {
    'single': PythonFunction(Single, 'single'),
    'undefined': UndefinedType(),
    'object': PythonFunction(ClassType, 'object')
}
