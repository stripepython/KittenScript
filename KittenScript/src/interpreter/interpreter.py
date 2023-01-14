import os
import sys
import traceback
from functools import lru_cache

from .context import Context
from .table import SymbolTable
from .values import (
    null, Single, Number, String, Bool,
    Value, List, Dict, auto, Namespace
)
from .. import constants, errors


class RTResult(object):
    def __init__(self):
        self.reset()
        
    def get(self):
        if not self.value:
            return None
        return self.value.get()
    
    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_continue = False
        self.loop_break = False
    
    def register(self, res):
        self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_continue = res.loop_continue
        self.loop_break = res.loop_break
        return res.value
    
    def success(self, value):
        self.reset()
        self.value = value
        return self
    
    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self
    
    def success_continue(self):
        self.reset()
        self.loop_continue = True
        return self
    
    def success_break(self):
        self.reset()
        self.loop_break = True
        return self
    
    def failure(self, error):
        self.reset()
        self.error = error
        return self
    
    def should_return(self):
        return bool(
            self.error or self.func_return_value or
            self.loop_continue or self.loop_break
        )


class Function(Value):
    class FunctionGetter(object):
        def __init__(self, func):
            self.func = func
        
        def __repr__(self):
            return self.func.__repr__()
        
        def execute(self, *args):
            return self.func.execute(*args)
    
    def __init__(self, name, body, arg_names, should_auto_return):
        super().__init__()
        self.name = name
        self.body = body
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return
    
    def __repr__(self):
        return f'<function {self.name}>'
    
    def copy(self):
        return (
            Function(self.name, self.body, self.arg_names, self.should_auto_return)
            .set_pos(self.pos_start, self.pos_end)
            .set_context(self.context)
        )
    
    def execute(self, args, res):
        res = RTResult()
        interpreter = Interpreter()
        new_context = Context(self.name, self.context, self.pos_start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        
        if len(args) != len(self.arg_names):
            return res.failure(errors.FunctionError(
                self.pos_start, self.pos_end,
                f'must {len(self.arg_names)} values, not {len(args)}', self.context
            ))
        for i in range(len(args)):
            arg_name = self.arg_names[i]
            arg_value = args[i]
            arg_value.set_context(new_context)
            new_context.symbol_table.set(arg_name, arg_value)
        
        value = res.register(interpreter.visit(self.body, new_context))
        if res.should_return() and res.func_return_value is None:
            return res
        return_value = (value if self.should_auto_return else None) or res.func_return_value or null.copy()
        return res.success(return_value)
    
    def get(self):
        return self.FunctionGetter(self)
    

class PythonFunction(Function):
    def __init__(self, py_func, name):
        super().__init__(name, None, None, True)
        self.func = py_func
        
    def __repr__(self):
        return f'<python-function {self.name}>'
    
    def copy(self):
        return PythonFunction(self.func, self.name).set_pos(self.pos_start, self.pos_end).set_context(self.context)
    
    def execute(self, args, res):
        try:
            result = self.func(*args)
        except (Exception, SystemExit) as err:
            return res.failure(errors.FunctionError(
                self.pos_start, self.pos_end,
                f'error in python-function: {err}', self.context
            ))
        if not isinstance(result, Value):
            return res.failure(errors.FunctionError(
                self.pos_start, self.pos_end,
                f'return value must be a value object', self.context
            ))
        return res.success(result)
    

class BuiltInFunction(PythonFunction):
    def __repr__(self):
        return f'<built-in function {self.name}>'
    
    def copy(self):
        return BuiltInFunction(self.func, self.name).set_pos(self.pos_start, self.pos_end).set_context(self.context)
    
    def execute(self, args, res):
        try:
            args = [i.get() for i in args]
            result = self.func(*args)
        except (Exception, SystemExit) as err:
            return res.failure(errors.FunctionError(
                self.pos_start, self.pos_end,
                str(err), self.context
            ))
        return res.success(auto(result))
    
    
class MemberFunction(Function):
    def __init__(self, value, func: Function):
        self.value = value
        self.func = func
        super().__init__(func.name, func.body, func.arg_names, func.should_auto_return)
      
    def __repr__(self):
        return f'<member-function {repr(self.func)}>'
      
    def copy(self):
        return (
            MemberFunction(self.value, self.func).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )
    
    def execute(self, args, res):
        return super().execute([self.value] + args, res)


class Interpreter(object):
    run_func = None
    
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        if not hasattr(self, method_name):
            raise AttributeError(f'No visit method named {method_name}')
        method = getattr(self, method_name)
        return method(node, context)
    
    @staticmethod
    @lru_cache(None)
    def visit_NumberNode(node, context):
        return RTResult().success(
            Number(node.token.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
    
    @staticmethod
    @lru_cache(None)
    def visit_StringNode(node, context):
        return RTResult().success(
            String(node.token.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
    
    @staticmethod
    @lru_cache(None)
    def visit_BoolNode(node, context):
        return RTResult().success(
            Bool(node.token.value)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
    
    @staticmethod
    @lru_cache(None)
    def visit_NullNode(node, context):
        return RTResult().success(
            null.copy()
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
    
    def visit_BinaryOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left, context))
        if res.should_return():
            return res
        
        right = res.register(self.visit(node.right, context))
        if res.should_return():
            return res
        
        result, error = left.binary_op(node.op.type, right)
        if error:
            return res.failure(error)
        return res.success(auto(result).set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        num = res.register(self.visit(node.right, context))
        if res.should_return():
            return res
        result, error = num.unary_op(node.op.type)
        if error:
            return res.failure(error)
        
        return res.success(auto(result).set_pos(node.pos_start, node.pos_end).set_context(context))
    
    @staticmethod
    def visit_VarAccessNode(node, context):
        res = RTResult()
        var_name = node.var_name.value
        value = context.symbol_table.get(var_name)
        if value == context.symbol_table.not_found:
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'"{var_name}" is not defined', context
            ))
        value = auto(value).set_pos(node.pos_start, node.pos_end).set_context(context)
        return res.success(value)
    
    def visit_VarAssignNode(self, node, context):
        res = RTResult()
        var_name = node.var_name.value
        value = res.register(self.visit(node.value, context))
        if res.should_return():
            return res

        if var_name.startswith('CONST'):
            if context.symbol_table.get(var_name) != context.symbol_table.not_found:
                return res.failure(errors.VariableError(
                    node.pos_start, node.pos_end,
                    f'cannot redefine the const variable {var_name}', context
                ))
        
        context.symbol_table.set(var_name, value)
        return res.success(auto(value).set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_IfNode(self, node, context):
        res = RTResult()
        
        for condition, comp, should_return_null in node.cases:
            condition_value = res.register(self.visit(condition, context))
            if res.should_return():
                return res
            
            if condition_value.is_true():
                comp_value = res.register(self.visit(comp, context))
                if res.should_return():
                    return res
                return res.success(
                    null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
                    if should_return_null else
                    comp_value.set_pos(node.pos_start, node.pos_end).set_context(context)
                )
        
        if node.else_case:
            else_case, should_return_null = node.else_case
            else_value = res.register(self.visit(else_case, context))
            if res.should_return():
                return res
            return res.success(
                null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
                if should_return_null else
                else_value.set_pos(node.pos_start, node.pos_end).set_context(context)
            )
        
        return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_ForNode(self, node, context):
        res = RTResult()
        elements = []
        var_name = node.var_name.value
        if var_name.startswith('CONST'):
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'cannot use the const variable "{var_name}" here', context
            ))
        
        start_value = Number(0)
        if node.start_value is not None:
            start_value = res.register(self.visit(node.start_value, context))
            if res.should_return():
                return res
            if not isinstance(start_value, Number):
                return res.failure(errors.VariableError(
                    start_value.pos_start, start_value.pos_end,
                    'must be a number', context
                ))
        
        end_value = res.register(self.visit(node.end_value, context))
        if res.should_return():
            return res
        if not isinstance(end_value, Number):
            return res.failure(errors.VariableError(
                end_value.pos_start, end_value.pos_end,
                'must be a number', context
            ))
        
        step_value = Number(1)
        if node.step_value is not None:
            step_value = res.register(self.visit(node.step_value, context))
            if res.should_return():
                return res
            if not isinstance(step_value, Number):
                return res.failure(errors.VariableError(
                    step_value.pos_start, step_value.pos_end,
                    'must be a number', context
                ))
        
        i = start_value.get()
        condition = (lambda: i < end_value.get()) if step_value.get() >= 0 else (lambda: i > end_value.get())
        flag = True
        
        while condition():
            context.symbol_table.set(var_name, Number(i))
            i += step_value.get()
            value = res.register(self.visit(node.body, context))
            
            if res.should_return() and (not res.loop_continue) and (not res.loop_break):
                return res
            if res.loop_continue:
                continue
            if res.loop_break:
                flag = False
                break
            elements.append(value)
            
        if flag:
            if node.else_body:
                res.register(self.visit(node.else_body, context))
                if res.should_return():
                    return res
        
        return res.success(
            null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
            if node.should_return_null else
            List(elements).set_pos(node.pos_start, node.pos_end).set_context(context)
        )
    
    def visit_WhileNode(self, node, context):
        res = RTResult()
        elements = []
        flag = True
        while True:
            condition = res.register(self.visit(node.condition, context))
            if res.should_return():
                return res
            if not condition.is_true():
                break
            
            value = res.register(self.visit(node.body, context))
            if res.should_return() and (not res.loop_continue) and (not res.loop_break):
                return res
            if res.loop_continue:
                continue
            if res.loop_break:
                flag = False
                break
            elements.append(value)
        if flag:
            if node.else_body:
                res.register(self.visit(node.else_body, context))
                if res.should_return():
                    return res
            
        return res.success(
            null.copy() if node.should_return_null else
            List(elements).set_pos(node.pos_start, node.pos_end).set_context(context)
        )
    
    def visit_ExitNode(self, node, context):
        res = RTResult()
        if node.status is None:
            sys.exit()
        status = res.register(self.visit(node.status, context))
        if res.should_return():
            return res
        status = status.get()
        if isinstance(status, (int, float)):
            sys.exit(int(status))
        raise SystemExit(str(status))
    
    def visit_ThrowNode(self, node, context):
        res = RTResult()
        if not node.details:
            return res.failure(errors.RTError(
                node.pos_start, node.pos_end,
                'no active exception to throw', context
            ))
        details = auto(res.register(self.visit(node.details, context)))
        if res.should_return():
            return res
        details = details.get()
        error_name = auto(res.register(self.visit(node.error_name, context)))
        if res.should_return():
            return res
        if not isinstance(error_name, String):
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                'error name must be string', context
            ))
        error_name = error_name.get()
        if not hasattr(errors, error_name):
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'no error named "{error_name}"', context
            ))
        if error_name == 'BaseError':
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                'cannot throw BaseError', context
            ))
        error_type = getattr(errors, error_name)
        try:
            return res.failure(error_type(node.pos_start, node.pos_end, details, context))
        except (TypeError, ValueError, RuntimeError):
            return res.failure(errors.RTError(
                node.pos_start, node.pos_end,
                'must throw a runtime-error', context
            ))
    
    @staticmethod
    def visit_FunctionNode(node, context):
        res = RTResult()
        func_name = (
            node.func_name if isinstance(node.func_name, str) else
            node.func_name.value
        )
        body = node.body
        arg_names = [i.value for i in node.arg_name]
        func_value = (
            Function(func_name, body, arg_names, node.should_auto_return)
            .set_pos(node.pos_start, node.pos_end)
            .set_context(context)
        )
        context.symbol_table.set(func_name, func_value)
        return res.success(func_value)
    
    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []
        func = res.register(self.visit(node.func, context))
        if res.should_return():
            return res
        func = func.copy().set_pos(node.pos_start, node.pos_end)
        
        for arg in node.arguments:
            args.append(res.register(self.visit(arg, context)))
            if res.should_return():
                return res
        
        return_value = res.register(func.execute(args, RTResult()))
        if res.should_return():
            return res
        return res.success(
            auto(return_value).set_pos(node.pos_start, node.pos_end).
            set_context(context)
        )
    
    def visit_IndexNode(self, node, context):
        res = RTResult()
        lst = res.register(self.visit(node.list, context))
        if res.should_return():
            return res
        index = res.register(self.visit(node.index, context))
        if res.should_return():
            return res
        result, error = lst.index_by(index)
        if error:
            return res.failure(error)
        return res.success(auto(result).set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []
        for element_node in node.items:
            elements.append(res.register(self.visit(element_node, context)))
            if res.should_return():
                return res
        return res.success(List(elements).set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_DictNode(self, node, context):
        res = RTResult()
        items = {}
        for key, value in node.items.items():
            key = res.register(self.visit(key, context))
            if res.should_return():
                return res
            key = key.get()
            value = res.register(self.visit(value, context))
            if res.should_return():
                return res
            try:
                items[key] = value
            except TypeError:
                return res.failure(errors.DictError(
                    node.pos_start, node.pos_end,
                    f'unhashable value: {key}', context
                ))
        return res.success(Dict(items).set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_IncludeNode(self, node, context):
        res = RTResult()
        module = res.register(self.visit(node.module, context))
        if res.should_return():
            return res
        if not isinstance(module.value, str):
            return res.failure(errors.IncludeError(
                node.pos_start, node.pos_end,
                'module name must be string', context
            ))
        cwd_path = os.path.join(os.getcwd(), module.value)
        interpreter_path = os.path.join(os.path.join(os.path.dirname(__file__), 'lib', module.value))
        if os.path.exists(cwd_path):
            return self._try_include(cwd_path, context, node)
        if os.path.exists(interpreter_path):
            return self._try_include(interpreter_path, context, node)
        return res.failure(errors.IncludeError(
            node.pos_start, node.pos_end,
            f'no module named {module.value}', context
        ))
    
    def _try_include(self, path: str, context, node):
        res = RTResult()
        lower = path.lower()
        py = ks = False
        for i in constants.PYTHON_MODULE:
            if lower.endswith(i):
                py = True
                break
        else:
            ks = True
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                code = f.read()
        except (FileNotFoundError, FileExistsError, PermissionError):
            return res.failure(errors.IncludeError(
                node.pos_start, node.pos_end,
                f'file {path} not found', context
            ))
        except UnicodeError:
            return res.failure(errors.IncludeError(
                node.pos_start, node.pos_end,
                f'the encoding of module file must be UTF-8', context
            ))
        except (Exception, SystemExit) as err:
            return res.failure(errors.IncludeError(
                node.pos_start, node.pos_end,
                f'cannot read file: {err}', context
            ))
        
        if py:
            _globals = {
                'functions': {}, 'PythonFunction': PythonFunction,
                'RTResult': RTResult, 'Single': Single, 'Value': Value,
                'List': List, 'Dict': Dict, 'Namespace': Namespace,
                'Bool': Bool, 'Number': Number, 'null': null.copy(),
                'auto': auto, 'String': String, 'true': Bool.true.copy(),
                'false': Bool.false.copy(), 'Function': Function,
                'MemberFunction': MemberFunction, 'BuiltInFunction': BuiltInFunction
            }
            try:
                compiled = compile(code, path, 'exec')
                exec(compiled, _globals)
            except (Exception, SystemExit):
                return res.failure(errors.IncludeError(
                    node.pos_start, node.pos_end,
                    f'python module error \n\n{traceback.format_exc()}', context
                ))
            
            functions = _globals.get('functions', {})
            if not isinstance(functions, dict):
                return res.failure(errors.IncludeError(
                    node.pos_start, node.pos_end,
                    f'python module error: functions must be dict', context
                ))
            
            for k, i in functions.items():
                functions[k] = i.set_pos(node.pos_start, node.pos_end).set_context(context)
            
            context.symbol_table.update(functions)
            return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
        
        elif ks:
            result, error, ctx = self.run_func(path, code)
            if error:
                return res.failure(error)
            context.symbol_table.update(ctx.symbol_table.symbols)
            return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
        
        else:
            return res.failure(errors.IncludeError(
                node.pos_start, node.pos_end,
                'not a python or src module', context
            ))
        
    def visit_ReturnNode(self, node, context):
        res = RTResult()
        value = null.copy()
        if node.return_value:
            value = res.register(self.visit(node.return_value, context))
            if res.should_return():
                return res
        return res.success_return(
            auto(value).set_pos(node.pos_start, node.pos_end).set_context(context)
        )
    
    @staticmethod
    def visit_ContinueNode(_, __):
        return RTResult().success_continue()

    @staticmethod
    def visit_BreakNode(_, __):
        return RTResult().success_break()
    
    def visit_TryNode(self, node, context):
        res = RTResult()
        try_res = res.register(self.visit(node.try_body, context))
        if not res.error:
            if node.else_body:
                res.register(self.visit(node.else_body, context))
                if res.should_return():
                    return res
            
            if node.finally_body:
                res.register(self.visit(node.finally_body, context))
                if res.should_return():
                    return res
                
            return res.success(
                null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
                if node.should_return_null else
                try_res.set_pos(node.pos_start, node.pos_end).set_context(context)
            )
        
        name, details = res.error.catch()
        context.symbol_table.set(node.catch_name.value, String(name))
        context.symbol_table.set(node.catch_details.value, String(details))
        catch_res = res.register(self.visit(node.catch_body, context))
        if node.finally_body:
            res.register(self.visit(node.finally_body, context))
            if res.should_return():
                return res
        if res.should_return():
            return res
        return res.success(
            null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
            if node.should_return_null else
            catch_res.set_pos(node.pos_start, node.pos_end).set_context(context)
        )
    
    @staticmethod
    def visit_DeleteNode(node, context):
        res = RTResult()
        value = context.symbol_table.remove(node.var_name.value)
        if value == context.symbol_table.not_found:
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'"{node.var_name.value}" is not defined', context
            ))
        if node.var_name.value.startswith('CONST_'):
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'cannot delete the const variable {node.var_name.value}', context
            ))
        return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_AssertNode(self, node, context):
        res = RTResult()
        condition = auto(res.register(self.visit(node.condition, context)))
        if res.should_return():
            return res
        details = ''
        if node.details:
            details = auto(res.register(self.visit(node.details, context))).get()
        if not condition.is_true():
            return res.failure(errors.AssertError(
                node.pos_start, node.pos_end, details, context
            ))
        return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_SwitchNode(self, node, context):
        res = RTResult()
        condition = auto(res.register(self.visit(node.condition, context)))
        if res.should_return():
            return res
        for expr, body, unless in node.cases:
            expr = auto(res.register(self.visit(expr, context)))
            if res.should_return():
                return res
            ee, error = condition.ee_by(expr)
            if error:
                return res.failure(error)
            if ee:
                unl = True
                if unless:
                    unless = auto(res.register(self.visit(unless, context)))
                    unl = not unless.is_true()
                if res.should_return():
                    return res
                if unl:
                    body = auto(res.register(self.visit(body, context)))
                    if res.should_return():
                        return res
                    return res.success(
                        body.set_pos(node.pos_start, node.pos_end).set_context(context)
                        if node.should_auto_return else
                        null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
                    )
        if node.default:
            default = auto(res.register(self.visit(node.default, context)))
            if res.should_return():
                return res
            return res.success(
                default.set_pos(node.pos_start, node.pos_end).set_context(context)
                if node.should_auto_return else
                null.copy().set_pos(node.pos_start, node.pos_end).set_context(context)
            )
        return res.success(null.copy().set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_OrNode(self, node, context):
        res = RTResult()
        left = auto(res.register(self.visit(node.left, context)))
        if res.should_return():
            return res
        if left.get():
            return res.success(left.set_pos(node.pos_start, node.pos_end).set_context(context))
        
        right = auto(res.register(self.visit(node.right, context)))
        if res.should_return():
            return res
        return res.success(right.set_pos(node.pos_start, node.pos_end).set_context(context))

    def visit_AndNode(self, node, context):
        res = RTResult()
        left = auto(res.register(self.visit(node.left, context)))
        if res.should_return():
            return res
        if not left.is_true():
            return res.success(left)
    
        right = auto(res.register(self.visit(node.right, context)))
        if res.should_return():
            return res
        return res.success(right)
    
    def visit_AttrAccessNode(self, node, context):
        res = RTResult()
        cls = res.register(self.visit(node.class_name, context))
        if res.error:
            return res
        attr, error = cls.getattr(node.attr_name.value)
        if error:
            return res.failure(error)
        if not isinstance(cls, Namespace):
            if isinstance(attr, Function) and (not isinstance(attr, MemberFunction)):
                attr = MemberFunction(cls, attr)
        return res.success(attr.set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_AttrAssignNode(self, node, context):
        res = RTResult()
        cls = context.symbol_table.get(node.class_name.value)
        if cls == context.symbol_table.not_found:
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'"{node.class_name.value}" is not defined', context
            ))
        value = res.register(self.visit(node.value, context))
        if res.error:
            return res
        cls.setattr(node.attr_name.value, value)
        return res.success(value.set_pos(node.pos_start, node.pos_end).set_context(context))
    
    def visit_NamespaceNode(self, node, context):
        res = RTResult()
        name = node.namespace_name.value
        new_context = Context(f'{name}', context, node.pos_start)
        new_context.symbol_table = SymbolTable(context.symbol_table)
        res.register(self.visit(node.body, new_context))
        if res.should_return():
            return res
        new_value = Namespace(name)
        for key, value in new_context.symbol_table.symbols.items():
            new_value.setattr(key, value)
        context.symbol_table.set(name, new_value)
        return res.success(new_value)
    
    @staticmethod
    def visit_UsingNode(node, context):
        res = RTResult()
        namespace = context.symbol_table.get(node.namespace_name.value)
        if namespace == context.symbol_table.not_found:
            return res.failure(errors.VariableError(
                node.pos_start, node.pos_end,
                f'namespace "{node.namespace_name.value}" is not defined', context
            ))
        if not isinstance(namespace, Namespace):
            return res.failure(errors.ClassError(
                node.pos_start, node.pos_end,
                f'"{node.namespace_name.value}" is not a namespace', context
            ))
        if node.func_name.type == constants.MUL:
            context.symbol_table.update(namespace.attrs)
        else:
            attr_name = node.func_name.value
            attr_value, error = namespace.getattr(attr_name)
            if error:
                return res.failure(error)
            context.symbol_table.set(attr_name, attr_value)
        return res.success(null.copy())
