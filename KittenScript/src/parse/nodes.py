from .. import constants
from ..tokens import Token


class SingleNode(object):
    def __init__(self, token):
        self.token = token
        
        self.pos_start = self.token.pos_start
        self.pos_end = self.token.pos_end
        
    def __repr__(self):
        return self.token.__repr__()
    
    def as_json(self):
        return {'type': 'single', 'token': self.token.as_json()}
    
    
class NumberNode(SingleNode):
    pass


class StringNode(SingleNode):
    pass


class BoolNode(SingleNode):
    pass


class NullNode(object):
    def __init__(self, token):
        self.pos_start = token.pos_start
        self.pos_end = token.pos_end
    
    @staticmethod
    def as_json():
        return {'type': 'null'}
    

class UnaryOpNode(object):
    def __init__(self, op, right):
        self.op = op
        self.right = right
        
        self.pos_start = self.op.pos_start
        self.pos_end = self.right.pos_end
        
    def __repr__(self):
        return f'({self.op}, {self.right})'
    
    def as_json(self):
        return {
            'type': 'unary',
            'op': self.op.as_json(),
            'number': self.right.as_json()
        }
    
    
class BinaryOpNode(object):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
        
        self.pos_start = self.left.pos_start
        self.pos_end = self.right.pos_end
        
    def __repr__(self):
        return f'({self.left}, {self.op}, {self.right})'
    
    def as_json(self):
        return {
            'type': 'binary',
            'left': self.left.as_json(),
            'op': self.op.as_json(),
            'right': self.right.as_json()
        }
    
    
class AndNode(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
        self.pos_start = self.left.pos_start
        self.pos_end = self.right.pos_end
        
    def as_json(self):
        return {
            'type': 'and',
            'left': self.left.as_json(),
            'right': self.right.as_json()
        }


class OrNode(object):
    def __init__(self, left, right):
        self.left = left
        self.right = right
        
        self.pos_start = self.left.pos_start
        self.pos_end = self.right.pos_end
        
    def as_json(self):
        return {
            'type': 'or',
            'left': self.left.as_json(),
            'right': self.right.as_json()
        }


class VarAccessNode(object):
    def __init__(self, var_name):
        self.var_name = var_name

        self.pos_start = self.var_name.pos_start
        self.pos_end = self.var_name.pos_end
        
    def __repr__(self):
        return f'[{self.var_name}]'
    
    def as_json(self):
        return {'type': 'var-access', 'name': self.var_name.as_json()}
        

class VarAssignNode(object):
    def __init__(self, var_name, value):
        self.var_name = var_name
        self.value = value

        self.pos_start = self.var_name.pos_start
        self.pos_end = self.value.pos_end
        
    def as_json(self):
        return {
            'type': 'var-assign',
            'name': self.var_name.as_json(),
            'value': self.value.as_json(),
        }
        

class IfNode(object):
    def __init__(self, cases, else_case):
        self.cases = cases
        self.else_case = else_case
        
        self.pos_start = self.cases[0][0].pos_start
        self.pos_end = (self.else_case or self.cases[-1])[0].pos_end
        
    def as_json(self):
        cases = []
        for condition, comp, should_return_null in self.cases:
            cases.append({
                'condition': condition.as_json(),
                'body': comp.as_json(),
                'oneline': not should_return_null,
            })
        else_case = None
        if self.else_case:
            else_case = {
                'body': self.else_case[0].as_json(),
                'oneline': not self.else_case[1],
            }
        return {
            'type': 'if',
            'cases': cases,
            'else-case': else_case
        }
            
            
class ForNode(object):
    def __init__(self, var_name, start_value, end_value, step_value,
                 body, should_return_null, else_body):
        self.var_name = var_name
        self.start_value = start_value
        self.end_value = end_value
        self.step_value = step_value
        self.body = body
        self.should_return_null = should_return_null
        self.else_body = else_body
        
        self.pos_start = self.var_name.pos_start
        self.pos_end = self.body.pos_end
        
    def as_json(self):
        return {
            'type': 'for',
            'name': self.var_name.as_json(),
            'start': self.start_value.as_json() if self.start_value else None,
            'end': self.end_value.as_json(),
            'step': self.step_value.as_json() if self.step_value else None,
            'body': self.body.as_json(),
            'oneline': not self.should_return_null,
            'else': self.else_body.as_json() if self.else_body else None,
        }
        
        
class WhileNode(object):
    def __init__(self, condition, body, should_return_null, else_body):
        self.condition = condition
        self.body = body
        self.should_return_null = should_return_null
        self.else_body = else_body
        
        self.pos_start = self.condition.pos_start
        self.pos_end = self.body.pos_end
        
    def as_json(self):
        return {
            'condition': self.condition.as_json(),
            'body': self.body.as_json(),
            'oneline': not self.should_return_null,
            'else': self.else_body.as_json() if self.else_body else None,
        }
        
        
class ExitNode(object):
    def __init__(self, status, pos_start, pos_end):
        self.status = status
        
        self.pos_start = pos_start
        self.pos_end = pos_end
        
    def as_json(self):
        return {
            'type': 'exit',
            'status': self.status.as_json() if self.status else None
        }
        
        
class ThrowNode(object):
    def __init__(self, error_name, details, pos_start=None, pos_end=None):
        self.error_name = error_name
        self.details = details
        
        self.pos_start = self.error_name.pos_start if self.error_name else pos_start
        self.pos_end = self.details.pos_end if self.error_name else pos_end
        
    def as_json(self):
        return {
            'type': 'throw',
            'error': self.error_name.as_json() if self.error_name else None,
            'details': self.details.as_json() if self.details else None,
        }


class FunctionNode(object):
    def __init__(self, func_name, arg_name, body, should_auto_return):
        self.func_name = func_name or '<lambda>'
        self.arg_name = arg_name
        self.body = body
        self.should_auto_return = should_auto_return

        self.pos_end = body.pos_end
        if func_name:
            self.pos_start = self.func_name.pos_start
        elif self.arg_name:
            self.pos_start = self.arg_name[0].pos_start
        else:
            self.pos_start = self.body.pos_start
            
    def as_json(self):
        if isinstance(self.func_name, str):
            name = Token(constants.STRING, self.func_name)
        else:
            name = self.func_name
        return {
            'type': 'function',
            'args': [i.as_json() for i in self.arg_name],
            'name': name.as_json(),
            'body': self.body.as_json(),
            'oneline': self.should_auto_return,
        }
            
            
class CallNode(object):
    def __init__(self, func, arguments):
        self.func = func
        self.arguments = arguments
        
        self.pos_start = self.func.pos_start
        if self.arguments:
            self.pos_end = self.arguments[-1].pos_end
        else:
            self.pos_end = self.func.pos_end
            
    def as_json(self):
        return {
            'type': 'call',
            'func': self.func.as_json(),
            'args': [i.as_json() for i in self.arguments],
        }
            

class IndexNode(object):
    def __init__(self, list_, index):
        self.list = list_
        self.index = index
        
        self.pos_start = self.list.pos_start
        self.pos_end = self.index.pos_end
        
    def as_json(self):
        return {
            'type': 'index',
            'object': self.list.as_json(),
            'index': self.index.as_json(),
        }
        
        
class ListNode(object):
    def __init__(self, items, pos_start=None, pos_end=None, is_block=False):
        self.items = items
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.is_block = is_block
        
    def as_json(self):
        return {
            'type': 'list',
            'items': [i.as_json() for i in self.items],
            'is-block': self.is_block,
        }
        

class DictNode(object):
    def __init__(self, items, pos_start=None, pos_end=None):
        self.items = items
        self.pos_start = pos_start
        self.pos_end = pos_end
        
    def as_json(self):
        return {
            'type': 'dict',
            'items': [(k.as_json(), v.as_json()) for k, v in self.items.items()],
        }


class IncludeNode(object):
    def __init__(self, module):
        self.module = module
        
        self.pos_start = self.module.pos_start
        self.pos_end = self.module.pos_end
        
    def as_json(self):
        return {
            'type': 'include',
            'module': self.module.as_json(),
        }
        
        
class ReturnNode(object):
    def __init__(self, return_value, pos_start, pos_end):
        self.return_value = return_value
        self.pos_start = pos_start
        self.pos_end = pos_end
        
    def as_json(self):
        return {
            'type': 'return',
            'value': self.return_value.as_json() if self.return_value else None,
        }
        
        
class ContinueNode(object):
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end
    
    @staticmethod
    def as_json():
        return {'type': 'continue'}
        

class BreakNode(object):
    def __init__(self, pos_start, pos_end):
        self.pos_start = pos_start
        self.pos_end = pos_end
    
    @staticmethod
    def as_json():
        return {'type': 'break'}
        
        
class TryNode(object):
    def __init__(self, try_body, catch_name, catch_details,
                 catch_body, should_return_null, else_body, finally_body):
        self.try_body = try_body
        self.catch_name = catch_name
        self.catch_details = catch_details
        self.catch_body = catch_body
        self.else_body = else_body
        self.finally_body = finally_body
        self.should_return_null = should_return_null
        
        self.pos_start = self.try_body.pos_start
        self.pos_end = (self.finally_body or self.catch_body).pos_end
        
    def as_json(self):
        return {
            'type': 'try',
            'try-body': self.try_body.as_json(),
            'name-var': self.catch_name.as_json(),
            'details-var': self.catch_details.as_json(),
            'catch-body': self.catch_body.as_json(),
            'else-body': self.else_body.as_json() if self.else_body else None,
            'finally-body': self.finally_body.as_json() if self.finally_body else None,
            'oneline': not self.should_return_null
        }
        

class DeleteNode(object):
    def __init__(self, var_name):
        self.var_name = var_name

        self.pos_start = self.var_name.pos_start
        self.pos_end = self.var_name.pos_end
        
    def as_json(self):
        return {
            'type': 'delete',
            'var': self.var_name.as_json(),
        }
        

class AssertNode(object):
    def __init__(self, condition, details):
        self.condition = condition
        self.details = details
        
        self.pos_start = self.condition.pos_start
        self.pos_end = self.condition.pos_end
        
    def as_json(self):
        return {
            'type': 'assert',
            'condition': self.condition.as_json(),
            'details': self.details.as_json() if self.details else None,
        }
        
        
class SwitchNode(object):
    def __init__(self, condition, cases, default, should_auto_return):
        self.condition = condition
        self.cases = cases
        self.default = default
        self.should_auto_return = should_auto_return
        
        self.pos_start = self.cases[0][-1].pos_start
        self.pos_end = (self.default or self.cases[-1][-1]).pos_end
        
    def as_json(self):
        cases = []
        for expr, body, unless in self.cases:
            cases.append({
                'match': expr.as_json(),
                'body': body.as_json(),
                'unless': unless.as_json() if unless else None,
            })
        return {
            'type': 'switch',
            'condition': self.condition.as_json(),
            'default': self.default.as_json() if self.default else None,
            'oneline': not self.should_auto_return,
            'cases': cases
        }
        

class AttrAccessNode(object):
    def __init__(self, class_name, attr_name):
        self.class_name = class_name
        self.attr_name = attr_name

        self.pos_start = self.class_name.pos_start
        self.pos_end = self.attr_name.pos_end
        
    def as_json(self):
        return {
            'type': 'attr-access',
            'class': self.class_name.as_json(),
            'attr': self.attr_name.as_json(),
        }
        
        
class AttrAssignNode(object):
    def __init__(self, class_name, attr_name, value):
        self.class_name = class_name
        self.attr_name = attr_name
        self.value = value

        self.pos_start = self.class_name.pos_start
        self.pos_end = self.attr_name.pos_end
        
    def as_json(self):
        return {
            'type': 'attr-assign',
            'class': self.class_name.as_json(),
            'attr': self.attr_name.as_json(),
            'value': self.value.as_json(),
        }
        
        
class NamespaceNode(object):
    def __init__(self, namespace_name, body):
        self.namespace_name = namespace_name
        self.body = body
        
        self.pos_start = self.namespace_name.pos_start
        self.pos_end = self.body.pos_end
        
    def as_json(self):
        return {
            'type': 'namespace',
            'body': self.body.as_json(),
        }
        
        
class UsingNode(object):
    def __init__(self, namespace_name, func_name):
        self.namespace_name = namespace_name
        self.func_name = func_name
        
        self.pos_start = self.namespace_name.pos_start
        self.pos_end = (self.func_name or self.namespace_name).pos_end
        
    def as_json(self):
        return {
            'type': 'using',
            'namespace': self.namespace_name.as_json(),
            'func': self.func_name.as_json()
        }
