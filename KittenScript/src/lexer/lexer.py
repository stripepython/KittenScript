from .. import constants, errors
from ..tokens import Token
from .position import Position


class LexerResult(object):
    token = None
    error = None
    
    def success(self, token: Token):
        self.token = token
        return self
    
    def failure(self, error):
        self.error = error
        return self


class Lexer(object):
    def __init__(self, file: str, code: str):
        self.file = file
        self.code = code
        self.in_paren = False
        
        self.current_char = None
        self.position = Position(-1, 0, -1, file, code)
        self.advance()
        self.defines = {}
        
    def advance(self):
        self.position.advance(self.current_char)
        if self.position.index < len(self.code):
            self.current_char = self.code[self.position.index]
        else:
            self.current_char = None

    def make_tokens(self):
        tokens = []
        while self.current_char:
            if self.current_char == '#':  # 注释
                self.skip_comment()
                continue
            
            if self.current_char in constants.WHITESPACES:  # 空格和制表符
                self.advance()
                continue
                
            if self.current_char == '\\':  # 当是\时，忽略后面的换行符
                self.advance()
                if self.current_char in constants.NEWLINE_CHAR:
                    self.advance()
                continue
                
            if self.current_char in constants.NEWLINE_CHAR:  # 换行
                if not self.in_paren:
                    tokens.append(Token(constants.NEWLINE, pos_start=self.position))
                self.advance()
                continue
                
            if self.current_char in constants.DIGITS:  # 数字
                res = self.make_number()
                if res.error:
                    return [], res.error
                tokens.append(res.token)
                continue
                
            if self.current_char in constants.LETTERS_DIGITS:  # 标识符或关键字
                tokens.append(self.make_identifier().token)
                continue
                
            if self.current_char in constants.OP_DICT:  # 操作符处理
                if self.current_char in constants.PAREN_START:
                    self.in_paren = True
                elif self.current_char in constants.PAREN_END:
                    self.in_paren = False
                op_info = constants.OP_DICT[self.current_char]
                tokens.append(self.make_operator(op_info[0], op_info[1]).token)
                continue
                
            if self.current_char in {'"', "'", '`'}:  # 字符串处理
                res = self.make_string(self.current_char)
                if res.error:
                    return [], res.error
                tokens.append(res.token)
                continue

            pos_start = self.position.copy()
            char = self.current_char
            self.advance()
            # 非法字符错误
            return [], errors.IllegalCharError(pos_start, self.position, f'"{char}"')
        
        tokens.append(Token(constants.EOF, pos_start=self.position))
        return tokens, None
    
    def skip_comment(self):
        self.advance()
        while self.current_char and self.current_char != '\n':
            self.advance()
    
    def make_number(self):
        res = LexerResult()
        num = ''
        dot = 0  # 是否有小数点
        pos_start = self.position.copy()
        while self.current_char and ((self.current_char in constants.DIGITS) or self.current_char in ('.', '_')):
            if self.current_char == '.':
                dot += 1
                if dot > 1:
                    break
            if self.current_char == '_':
                self.advance()
                continue
            num += self.current_char
            self.advance()
            
        if dot:
            if num == '.':  # 如果只有一个".",就是分隔符
                return res.success(Token(constants.POINT, pos_start=self.position))
            return res.success(Token(constants.FLOAT, float(num), pos_start, self.position))
        
        return res.success(Token(constants.INT, int(num), pos_start, self.position))
    
    def make_identifier(self):
        res = LexerResult()
        name = ''
        pos_start = self.position.copy()
        
        while self.current_char and (self.current_char in constants.LETTERS_DIGITS):
            name += self.current_char
            self.advance()
        
        if name in self.defines:
            name = self.defines.get(name)
        if name in constants.KEYWORDS:
            if name in constants.SPECIAL_KEYWORDS:
                type_, value = constants.SPECIAL_KEYWORDS[name]
                return res.success(Token(type_, value, pos_start, self.position))
            tok_type = constants.KEYWORD
        else:
            tok_type = constants.IDENTIFIER
            
        return res.success(Token(tok_type, name, pos_start, self.position))
    
    def make_operator(self, start_type: str, expectation_dict: dict):
        res = LexerResult()
        tok_type = start_type
        pos_start = self.position.copy()
        
        self.advance()
        for expectation, type_ in expectation_dict.items():
            if self.current_char == expectation:
                self.advance()
                tok_type = type_
                break
        
        return res.success(Token(tok_type, pos_start=pos_start, pos_end=self.position))
    
    def make_string(self, quotation):
        res = LexerResult()
        string = ''
        pos_start = self.position.copy()
        escape_character = False
        
        self.advance()
        while self.current_char != quotation or escape_character:
            if not self.current_char or self.current_char == '\n':
                # Excepted "'", '"' or "`"
                details = 'Excepted \'"\'' if quotation == '"' else f'Excepted "{quotation}"'
                return res.failure(errors.InvalidSyntaxError(pos_start, self.position, details))
            if escape_character:
                # 转义字符
                string += constants.ESCAPE_CHARACTERS.get(self.current_char, self.current_char)
                escape_character = False
                self.advance()
                continue
            # `...`类似于r'...'，参考python2
            if self.current_char == '\\' and quotation != '`':
                escape_character = True
                self.advance()
                continue
            string += self.current_char
            self.advance()
            
        self.advance()
        return res.success(Token(constants.STRING, string, pos_start, self.position))
