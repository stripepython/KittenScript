def _strings_with_arrows(text: str, pos_start, pos_end):
    res = ''
    idx_start = max(text.rfind('\n', 0, pos_start.index), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0:
        idx_end = len(text)
    line_count = pos_end.line - pos_start.line + 1
    for i in range(line_count):
        line = text[idx_start:idx_end]
        col_start = pos_start.column if i == 0 else 0
        col_end = pos_end.column if i == line_count - 1 else len(line) - 1
        
        res += line + '\n'
        res += ' ' * col_start + '^' * (col_end - col_start)
        
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0:
            idx_end = len(text)
    return res.replace('\t', '')


class BaseError(object):
    def __init__(self, pos_start, pos_end, error_name: str, details: str):
        self.pos_start = pos_start.copy()
        self.pos_end = pos_end.copy()
        self.error_name = error_name
        self.details = details
    
    def as_string(self):
        res = f'{self.error_name}: {self.details}\n'
        res += f'File {self.pos_start.file}, line {self.pos_end.line + 1}'
        res += '\n' + _strings_with_arrows(self.pos_start.text, self.pos_start, self.pos_end)
        return res
    
    
class IllegalCharError(BaseError):
    # 无效字符错误
    def __init__(self, pos_start, pos_end, details: str):
        super().__init__(pos_start, pos_end, 'Illegal Character Error', details)
        
        
class InvalidSyntaxError(BaseError):
    # 无效语法错误
    def __init__(self, pos_start, pos_end, details: str):
        super().__init__(pos_start, pos_end, 'Invalid Syntax Error', details)
        

class OutsideError(BaseError):
    def __init__(self, pos_start, pos_end, details: str):
        super().__init__(pos_start, pos_end, 'Outside Error', details)
        
        
class RTError(BaseError):
    # 运行时错误
    def __init__(self, pos_start, pos_end, details: str, context, error_name: str = 'Runtime Error'):
        self.context = context
        super().__init__(pos_start, pos_end, error_name, details)
        
    def catch(self):
        return 'RTError', self.details
        
    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}\n'
        result += '\n' + _strings_with_arrows(self.pos_start.text, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        res = ''
        pos = self.pos_start
        ctx = self.context
        while ctx:
            res = f'\tFile {pos.file}, line {pos.line + 1}, in {ctx.display_name}\n' + res
            pos = ctx.parent_entry_pos
            ctx = ctx.parent
        return 'Traceback (most recent call last):\n' + res


class MathError(RTError):
    # 算术错误
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'Math Error')
        
    def catch(self):
        return 'MathError', self.details
        
        
class VariableError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'Variable Error')
        
    def catch(self):
        return 'VariableError', self.details
        

class FunctionError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'Function Error')
        
    def catch(self):
        return 'FunctionError', self.details
        
        
class ListError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'List Error')
        
    def catch(self):
        return 'ListError', self.details
        
        
class IncludeError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'Include Error')
        
    def catch(self):
        return 'IncludeError', self.details


class DictError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'Dict Error')
    
    def catch(self):
        return 'DictError', self.details
    
    
class AssertError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'AssertError')
    
    def catch(self):
        return 'AssertError', self.details


class ClassError(RTError):
    def __init__(self, pos_start, pos_end, details: str, context):
        super().__init__(pos_start, pos_end, details, context, 'ClassError')
    
    def catch(self):
        return 'ClassError', self.details
