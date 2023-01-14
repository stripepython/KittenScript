from typing import List

from . import nodes
from .. import constants, errors
from ..tokens import Token


class ParserResult(object):
    node = None
    error = None
    error_token = None
    advance_count = 0
    to_reverse_count = 0
    last_registered_advance_count = 0
    
    def __repr__(self):
        return f'<node={self.node}, error={self.error}>'
    
    def success(self, node):
        self.node = node
        return self
    
    def failure(self, error):
        self.error = error
        return self
    
    def register(self, result):
        if isinstance(result, ParserResult):
            self.last_registered_advance_count = result.advance_count
            self.advance_count += result.advance_count
            if result.error:
                self.error = result.error
                return self
            return result.node
        return self
    
    def register_advancement(self):
        self.advance_count += 1
        self.last_registered_advance_count = 1
        
    def try_register(self, res):
        if isinstance(res, ParserResult):
            if res.error:
                self.to_reverse_count = res.advance_count
                return None
            return self.register(res)
        return res
    

class Parser(object):
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = -1
        self.current_token = None
        self.advance()
        
        self.in_loop = False
        self.in_func = False
        
    def advance(self):
        self.index += 1
        self.update()
        return self.current_token
    
    def update(self):
        if 0 <= self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
            
    def reverse(self, amount=1):
        self.index -= amount
        self.update()
        return self.current_token
    
    def factor(self):
        res = ParserResult()
        tok = self.current_token
        
        if tok.type in constants.TYPES:
            res.register(self.advance())
            res.register_advancement()
            if tok.type in (constants.INT, constants.FLOAT):
                return res.success(nodes.NumberNode(tok))
            if tok.type == constants.STRING:
                return res.success(nodes.StringNode(tok))
            if tok.type == constants.BOOL:
                return res.success(nodes.BoolNode(tok))
            if tok.type == constants.NULL:
                return res.success(nodes.NullNode(tok))
            return res.failure(errors.InvalidSyntaxError(
                tok.pos_start, self.current_token.pos_end,
                'invalid token'
            ))
        
        if tok.type == constants.IDENTIFIER:
            res.register(self.advance())
            res.register_advancement()
            
            return res.success(nodes.VarAccessNode(tok))
        
        if (tok.type in constants.UNARY_OP) or tok.matches(constants.KEYWORD, 'not'):
            res.register(self.advance())
            res.register_advancement()
            factor = res.register(self.factor())
            if res.error:
                return res
            if tok.matches(constants.KEYWORD, 'not'):
                a, b = tok.pos_start, tok.pos_end
                tok = Token(constants.NOT, pos_start=a, pos_end=b)
            return res.success(nodes.UnaryOpNode(tok, factor))

        if tok.type == constants.LPAREN:
            res.register(self.advance())
            res.register_advancement()
            node = res.register(self.expr())
            if res.error:
                return res
            if self.current_token.type != constants.RPAREN:
                return res.failure(errors.InvalidSyntaxError(
                    tok.pos_start, self.current_token.pos_end,
                    'excepted ")"'
                ))
            res.register(self.advance())
            res.register_advancement()
            return res.success(node)
        
        if self.current_token.type == constants.LBRACKET:
            list_expr = res.register(self.list_expr())
            if res.error:
                return res
            return res.success(list_expr)
        
        if self.current_token.type == constants.LBRACE:
            dict_expr = res.register(self.dict_expr())
            if res.error:
                return res
            return res.success(dict_expr)
        
        return res.failure(errors.InvalidSyntaxError(
            tok.pos_start, self.current_token.pos_end,
            'invalid token'
        ))
    
    def var_expr(self):
        # var-expr -> VAR <identifier> EQ comp
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'var'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "var"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
    
        var_name = self.current_token
        res.register(self.advance())
        res.register_advancement()
        op = None
        if self.current_token.type in constants.MATH_BINARY_OP:
            op = self.current_token
            res.register(self.advance())
            res.register_advancement()
        if self.current_token.type != constants.EQ:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "="'
            ))
    
        res.register(self.advance())
        res.register_advancement()
        value = res.register(self.expr())
        if res.error:
            return res
        if op:
            value = nodes.BinaryOpNode(nodes.VarAccessNode(var_name), op, value)
        return res.success(nodes.VarAssignNode(var_name, value))
    
    def if_expr(self):
        # if-expr ::= if-expr-a | if-expr-b
        # if-expr-a ::= IF comp THEN [{ELIF comp THEN}] [ELSE comp]
        # if-expr-b ::= IF comp THEN NEWLINE program [{ELIF comp THEN NEWLINE program}] [ELSE NEWLINE program] END
        res = ParserResult()
        all_cases = res.register(self.if_expr_if())
        if res.error:
            return res
        cases, else_case = all_cases
        return res.success(nodes.IfNode(cases, else_case))
    
    def if_expr_if(self):
        return self.if_expr_cases('if')
    
    def if_expr_elif(self):
        return self.if_expr_cases('elif')
    
    def if_expr_else(self):
        res = ParserResult()
        else_case = None
        if self.current_token.matches(constants.KEYWORD, 'else'):
            res.register(self.advance())
            res.register_advancement()
            
            if self.current_token.type == constants.NEWLINE:
                res.register(self.advance())
                res.register_advancement()
                
                stmt = res.register(self.program())
                if res.error:
                    return res
                stmt.is_block = True
                else_case = (stmt, True)
                
                if not self.current_token.matches(constants.KEYWORD, 'end'):
                    return res.failure(errors.InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        f'excepted "end"'
                    ))

                res.register(self.advance())
                res.register_advancement()
            
            else:
                stmt = res.register(self.stmt())
                if res.error:
                    return res
                else_case = (stmt, False)
        return res.success(else_case)
    
    def if_expr_end(self):
        res = ParserResult()
        cases, else_case = [], None
        if self.current_token.matches(constants.KEYWORD, 'elif'):
            all_cases = res.register(self.if_expr_elif())
            if res.error:
                return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_else())
            if res.error:
                return res
        return res.success((cases, else_case))
    
    def if_expr_cases(self, case_keyword):
        res = ParserResult()
        cases = []
        else_case = None
        if not self.current_token.matches(constants.KEYWORD, case_keyword):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                f'excepted "{case_keyword}"'
            ))
    
        res.register(self.advance())
        res.register_advancement()
        condition = res.register(self.expr())
        if res.error:
            return res
        if not self.current_token.matches(constants.KEYWORD, 'then'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "then"'
            ))
        res.register(self.advance())
        res.register_advancement()
        
        if self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            stmt = res.register(self.program())
            if res.error:
                return res
            stmt.is_block = True
            cases.append((condition, stmt, True))
            
            if self.current_token.matches(constants.KEYWORD, 'end'):
                res.register(self.advance())
                res.register_advancement()
                return res.success((cases, else_case))
                
        else:
            stmt = res.register(self.stmt())
            if res.error:
                return res
            cases.append((condition, stmt, False))

        all_cases = res.register(self.if_expr_end())
        if res.error:
            return res
        new_cases, else_case = all_cases
        return res.success((cases + new_cases, else_case))
    
    def for_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'for'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "for"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        var_name = self.current_token
        
        res.register(self.advance())
        res.register_advancement()
        start_value = None
        if self.current_token.type == constants.EQ:
            res.register(self.advance())
            res.register_advancement()
            start_value = res.register(self.expr())
            if res.error:
                return res
            
        if not self.current_token.matches(constants.KEYWORD, 'to'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "to"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        end_value = res.register(self.expr())
        if res.error:
            return res
        
        step_value = None
        if self.current_token.matches(constants.KEYWORD, 'step'):
            res.register(self.advance())
            res.register_advancement()
            step_value = res.register(self.expr())
            if res.error:
                return res

        if not self.current_token.matches(constants.KEYWORD, 'then'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "then"'
            ))
        res.register(self.advance())
        res.register_advancement()
        flag = True
        else_body = None
        self.in_loop = True
        if self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            body = res.register(self.program())
            if res.error:
                return res
            body.is_block = True
            
            c = ' or "else"'
            if self.current_token.matches(constants.KEYWORD, 'else'):
                res.register(self.advance())
                res.register_advancement()
                else_body = res.register(self.program())
                if res.error:
                    return res
                else_body.is_block = True
                c = ''

            if not self.current_token.matches(constants.KEYWORD, 'end'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted "end"' + c
                ))
            res.register(self.advance())
            res.register_advancement()
            
        else:
            body = res.register(self.stmt())
            flag = False
            
        if res.error:
            return res
        self.in_loop = False
        return res.success(nodes.ForNode(
            var_name, start_value, end_value,
            step_value, body, flag, else_body
        ))
    
    def while_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'while'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "while"'
            ))
        res.register(self.advance())
        res.register_advancement()
        condition = res.register(self.expr())
        if res.error:
            return res
        if not self.current_token.matches(constants.KEYWORD, 'then'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "then"'
            ))
        res.register(self.advance())
        res.register_advancement()
        
        flag = True
        else_body = None
        self.in_loop = True
        if self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            body = res.register(self.program())
            if res.error:
                return res
            body.is_block = True
            
            c = ' or "else"'
            if self.current_token.matches(constants.KEYWORD, 'else'):
                res.register(self.advance())
                res.register_advancement()
                else_body = res.register(self.program())
                if res.error:
                    return res
                else_body.is_block = True
                c = ''
    
            if not self.current_token.matches(constants.KEYWORD, 'end'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted "end"' + c
                ))
            res.register(self.advance())
            res.register_advancement()
            
        else:
            body = res.register(self.stmt())
            flag = False
        if res.error:
            return res
        self.in_loop = False
        
        return res.success(nodes.WhileNode(condition, body, flag, else_body))
    
    def switch_expr_cases(self, should_auto_return, first, res: ParserResult):
        body = res.register(self.expr() if should_auto_return else self.program())
        if res.error:
            return res
        cases = [(first[0], body, first[1])]
        
        while self.current_token.matches(constants.KEYWORD, 'case'):
            res.register(self.advance())
            res.register_advancement()
            expr = res.register(self.expr())
            if res.error:
                return res
            unless = None
            if self.current_token.matches(constants.KEYWORD, 'unless'):
                res.register(self.advance())
                res.register_advancement()
                unless = res.register(self.expr())
                if res.error:
                    return res
            if not self.current_token.matches(constants.KEYWORD, 'then'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted "then"'
                ))
            res.register(self.advance())
            res.register_advancement()

            body = res.register(self.expr() if should_auto_return else self.program())
            if res.error:
                return res
            if isinstance(body, nodes.ListNode):
                body.is_block = True
            cases.append((expr, body, unless))
            
        return cases
    
    def switch_expr_default(self, should_auto_return, res: ParserResult):
        if not self.current_token.matches(constants.KEYWORD, 'default'):
            return None
        res.register(self.advance())
        res.register_advancement()
        default = res.register(self.expr() if should_auto_return else self.program())
        if res.error:
            return res
        if isinstance(default, nodes.ListNode):
            default.is_block = True
        return default
        
    def switch_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'switch'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "switch"'
            ))

        res.register(self.advance())
        res.register_advancement()
        condition = res.register(self.expr())
        if res.error:
            return res
        
        flag = True
        if self.current_token.type == constants.NEWLINE:
            self.blanks(res)
            flag = False
            
        if not self.current_token.matches(constants.KEYWORD, 'case'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "case"'
            ))
        res.register(self.advance())
        res.register_advancement()
        expr = res.register(self.expr())
        if res.error:
            return res
        unless = None
        if self.current_token.matches(constants.KEYWORD, 'unless'):
            res.register(self.advance())
            res.register_advancement()
            unless = res.register(self.expr())
            if res.error:
                return res
        if not self.current_token.matches(constants.KEYWORD, 'then'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "then"'
            ))
        res.register(self.advance())
        res.register_advancement()
        
        cases = self.switch_expr_cases(flag, (expr, unless), res)
        if res.error:
            return res
        default = self.switch_expr_default(flag, res)
        if res.error:
            return res
        if not (flag or self.current_token.matches(constants.KEYWORD, 'end')):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "end"'
            ))
        res.register(self.advance())
        res.register_advancement()
        
        return res.success(nodes.SwitchNode(condition, cases, default, flag))
    
    def func_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'function'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "function"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        var_name = self.current_token
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.LPAREN:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "("'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        arg_name = []
        if self.current_token.type == constants.IDENTIFIER:
            arg_name.append(self.current_token)
            res.register(self.advance())
            res.register_advancement()
            while self.current_token.type == constants.COMMA:
                res.register(self.advance())
                res.register_advancement()
                if self.current_token.type != constants.IDENTIFIER:
                    return res.failure(errors.InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        'excepted an identifier'
                    ))
                arg_name.append(self.current_token)
                res.register(self.advance())
                res.register_advancement()

        if self.current_token.type != constants.RPAREN:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted ")"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        flag = False
        self.in_func = True
        if self.current_token.matches(constants.KEYWORD, 'do'):
            res.register(self.advance())
            res.register_advancement()
            body = res.register(self.expr())
            flag = True
        else:
            res.register(self.advance())
            res.register_advancement()
            body = res.register(self.program())
            if res.error:
                return res
            body.is_block = True
            if not self.current_token.matches(constants.KEYWORD, 'end'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    f'excepted "end"'
                ))
            res.register(self.advance())
            res.register_advancement()
        
        if res.error:
            return res
        self.in_func = False
        return res.success(nodes.FunctionNode(var_name, arg_name, body, flag))
    
    def lambda_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'lambda'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "lambda"'
            ))
        res.register(self.advance())
        res.register_advancement()
        arg_name = []
        if not self.current_token.matches(constants.KEYWORD, 'do'):
            if self.current_token.type != constants.IDENTIFIER:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted an identifier'
                ))
            arg_name.append(self.current_token)
            res.register(self.advance())
            res.register_advancement()
            while self.current_token.type == constants.COMMA:
                res.register(self.advance())
                res.register_advancement()
                if self.current_token.type != constants.IDENTIFIER:
                    return res.failure(errors.InvalidSyntaxError(
                        self.current_token.pos_start, self.current_token.pos_end,
                        'excepted an identifier'
                    ))
                arg_name.append(self.current_token)
                res.register(self.advance())
                res.register_advancement()
            if not self.current_token.matches(constants.KEYWORD, 'do'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted "do"'
                ))
        res.register(self.advance())
        res.register_advancement()
        expr = res.register(self.expr())
        if res.error:
            return res
        return res.success(nodes.FunctionNode(None, arg_name, expr, True))
    
    def namespace_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'namespace'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "namespace"'
            ))
        res.register(self.advance())
        res.register_advancement()
        identifier = self.current_token
        if identifier.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        res.register(self.advance())
        res.register_advancement()
        body = res.register(self.program())
        if not self.current_token.matches(constants.KEYWORD, 'end'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "end"'
            ))
        body.is_block = True
        res.register(self.advance())
        res.register_advancement()
        return res.success(nodes.NamespaceNode(identifier, body))
    
    def using_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'using'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "using"'
            ))
        res.register(self.advance())
        res.register_advancement()
        identifier = self.current_token
        if identifier.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.POINT:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "."'
            ))
        res.register(self.advance())
        res.register_advancement()
        
        func = self.current_token
        if func.type not in (constants.IDENTIFIER, constants.MUL):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier or "*"'
            ))
        res.register(self.advance())
        res.register_advancement()
        return res.success(nodes.UsingNode(identifier, func))
        
    def try_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'try'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "try"'
            ))
        res.register(self.advance())
        res.register_advancement()
        flag = True
        if self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            try_body = res.register(self.program())
        else:
            try_body = res.register(self.stmt())
            flag = False
        if res.error:
            return res
        if flag:
            try_body.is_block = True
        if not self.current_token.matches(constants.KEYWORD, 'catch'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "catch"'
            ))
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        
        catch_name = self.current_token
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.COMMA:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted ","'
            ))
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        catch_details = self.current_token
        res.register(self.advance())
        res.register_advancement()
        if not self.current_token.matches(constants.KEYWORD, 'then'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "then"'
            ))
        res.register(self.advance())
        res.register_advancement()
        else_body = None
        finally_body = None
        
        if self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            catch_body = res.register(self.program())
            if res.error:
                return res
            catch_body.is_block = True
            if self.current_token.matches(constants.KEYWORD, 'else'):
                res.register(self.advance())
                res.register_advancement()
                else_body = res.register(self.program())
                if res.error:
                    return res
                else_body.is_block = True
            
            if self.current_token.matches(constants.KEYWORD, 'finally'):
                res.register(self.advance())
                res.register_advancement()
                finally_body = res.register(self.program())
                if res.error:
                    return res
                finally_body.is_block = True
                
            if not self.current_token.matches(constants.KEYWORD, 'end'):
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted "end"'
                ))
            res.register(self.advance())
            res.register_advancement()
        else:
            catch_body = res.register(self.stmt())
            flag = False
        if res.error:
            return res
        return res.success(nodes.TryNode(
            try_body, catch_name, catch_details, catch_body, flag, else_body, finally_body
        ))

    def assert_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'assert'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "assert"'
            ))
        res.register(self.advance())
        res.register_advancement()
        condition = res.register(self.expr())
        if res.error:
            return res
        details = None
        if self.current_token.type == constants.COMMA:
            res.register(self.advance())
            res.register_advancement()
            details = res.register(self.expr())
            if res.error:
                return res
        return res.success(nodes.AssertNode(condition, details))
    
    def call(self, func=None):
        res = ParserResult()
        if self.current_token.type != constants.LPAREN:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "("'
            ))
        res.register(self.advance())
        res.register_advancement()
        arguments = []
        if self.current_token.type == constants.RPAREN:
            res.register(self.advance())
            res.register_advancement()
        else:
            arguments.append(res.register(self.expr()))
            if res.error:
                return res
            while self.current_token.type == constants.COMMA:
                res.register(self.advance())
                res.register_advancement()
                arguments.append(res.register(self.expr()))
                if res.error:
                    return res
            if self.current_token.type != constants.RPAREN:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted ")"'
                ))
            res.register(self.advance())
            res.register_advancement()
        
        call = res.register(self.index_or_call(nodes.CallNode(func, arguments)))
        if res.error:
            return res
        return res.success(call)
    
    def index_expr(self, list_=None):
        res = ParserResult()
        if self.current_token.type != constants.LBRACKET:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "["'
            ))
        res.register(self.advance())
        res.register_advancement()
        expr = res.register(self.expr())
        if res.error:
            return res
        if self.current_token.type != constants.RBRACKET:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "]"'
            ))
        res.register(self.advance())
        res.register_advancement()
        index = res.register(self.index_or_call(nodes.IndexNode(list_, expr)))
        if res.error:
            return res
        return res.success(index)
    
    def list_expr(self):
        res = ParserResult()
        pos_start = self.current_token.pos_start.copy()
        if self.current_token.type != constants.LBRACKET:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "["'
            ))
        res.register(self.advance())
        res.register_advancement()
        self.blanks(res)
        if self.current_token.type == constants.RBRACKET:
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.ListNode([], pos_start, self.current_token.pos_end.copy()))
        items = [res.register(self.expr())]
        if res.error:
            return res
        while self.current_token.type == constants.COMMA:
            res.register(self.advance())
            res.register_advancement()
            self.blanks(res)
            items.append(res.register(self.expr()))
            if res.error:
                return res
        self.blanks(res)
        if self.current_token.type != constants.RBRACKET:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "]"'
            ))
        res.register(self.advance())
        res.register_advancement()
        return res.success(nodes.ListNode(items, pos_start, self.current_token.pos_end.copy()))
    
    def dict_expr(self):
        res = ParserResult()
        pos_start = self.current_token.pos_start.copy()
        if self.current_token.type != constants.LBRACE:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "{"'
            ))
        res.register(self.advance())
        res.register_advancement()
        self.blanks(res)
        if self.current_token.type == constants.RBRACE:
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.DictNode({}, pos_start, self.current_token.pos_end.copy()))
        
        items = {}
        key = res.register(self.expr())
        if res.error:
            return res
        if self.current_token.type != constants.COLON:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted ":"'
            ))
        res.register(self.advance())
        res.register_advancement()
        self.blanks(res)
        value = res.register(self.expr())
        if res.error:
            return res
        items[key] = value
        while self.current_token.type == constants.COMMA:
            res.register(self.advance())
            res.register_advancement()
            self.blanks(res)
            key = res.register(self.expr())
            if res.error:
                return res
            if self.current_token.type != constants.COLON:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted ":"'
                ))
            res.register(self.advance())
            res.register_advancement()
            self.blanks(res)
            value = res.register(self.expr())
            if res.error:
                return res
            items[key] = value
        
        self.blanks(res)
        if self.current_token.type != constants.RBRACE:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "}"'
            ))
        res.register(self.advance())
        res.register_advancement()
        return res.success(nodes.DictNode(items, pos_start, self.current_token.pos_end.copy()))
    
    def set_expr(self):
        res = ParserResult()
        if not self.current_token.matches(constants.KEYWORD, 'attr'):
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "attr"'
            ))
        
        res.register(self.advance())
        res.register_advancement()
        class_name = self.current_token
        if class_name.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        res.register(self.advance())
        res.register_advancement()
        if self.current_token.type != constants.POINT:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "."'
            ))
        res.register(self.advance())
        res.register_advancement()
        attr_name = self.current_token
        if attr_name.type != constants.IDENTIFIER:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted an identifier'
            ))
        res.register(self.advance())
        res.register_advancement()
        op = None
        if self.current_token.type in constants.MATH_BINARY_OP:
            op = self.current_token
            res.register(self.advance())
            res.register_advancement()
        if self.current_token.type != constants.EQ:
            return res.failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'excepted "="'
            ))
        res.register(self.advance())
        res.register_advancement()
        expr = res.register(self.expr())
        if res.error:
            return res
        if op:
            expr = nodes.BinaryOpNode(nodes.AttrAccessNode(
                nodes.VarAccessNode(class_name), attr_name), op, expr
            )
        return res.success(nodes.AttrAssignNode(class_name, attr_name, expr))

    def blanks(self, res):
        cnt = 0
        while self.current_token.type == constants.NEWLINE:
            res.register(self.advance())
            res.register_advancement()
            cnt += 1
        return cnt
    
    def expr(self):
        """
        expr ::= (comp-expr ((AND | OR) comp-expr)* ) | if-expr | for-expr | exit-expr | throw-expr |
                 while-expr | var-expr | func-expr | include-expr | try-expr | del-expr | switch-expr |
                 lambda-expr | assert-expr
        """
        res = ParserResult()
        tok = self.current_token
    
        if tok.matches(constants.KEYWORD, 'var'):
            var_expr = res.register(self.var_expr())
            if res.error:
                return res
            return res.success(var_expr)
    
        if tok.matches(constants.KEYWORD, 'if'):
            if_expr = res.register(self.if_expr())
            if res.error:
                return res
            return res.success(if_expr)
    
        if tok.matches(constants.KEYWORD, 'for'):
            for_expr = res.register(self.for_expr())
            if res.error:
                return res
            return res.success(for_expr)
    
        if tok.matches(constants.KEYWORD, 'exit'):
            # exit-expr ::= EXIT [comp]
            pos_start = self.current_token.pos_start.copy()
            res.register(self.advance())
            res.register_advancement()
            status = res.try_register(self.expr())
            if res.error:
                return res
            if status is None:
                self.reverse(res.to_reverse_count)
            return res.success(nodes.ExitNode(status, pos_start, self.current_token.pos_end.copy()))
    
        if tok.matches(constants.KEYWORD, 'throw'):
            pos_start = tok.pos_start
            res.register(self.advance())
            res.register_advancement()
            error_name = res.try_register(self.expr())
            if error_name is None:
                res.register(self.reverse(res.to_reverse_count))
                return res.success(nodes.ThrowNode(
                    None, None, pos_start, self.current_token.pos_end.copy()
                ))
            if self.current_token.type != constants.COMMA:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted ","'
                ))
            res.register(self.advance())
            res.register_advancement()
            expr = res.register(self.expr())
            if res.error:
                return res
            return res.success(nodes.ThrowNode(error_name, expr))
    
        if tok.matches(constants.KEYWORD, 'while'):
            while_expr = res.register(self.while_expr())
            if res.error:
                return res
            return res.success(while_expr)
    
        if tok.matches(constants.KEYWORD, 'function'):
            func_expr = res.register(self.func_expr())
            if res.error:
                return res
            return res.success(func_expr)
    
        if tok.matches(constants.KEYWORD, 'lambda'):
            lambda_expr = res.register(self.lambda_expr())
            if res.error:
                return res
            return res.success(lambda_expr)
    
        if tok.matches(constants.KEYWORD, 'include'):
            res.register(self.advance())
            res.register_advancement()
            module = res.register(self.expr())
            if res.error:
                return res
            return res.success(nodes.IncludeNode(module))
    
        if tok.matches(constants.KEYWORD, 'try'):
            try_expr = res.register(self.try_expr())
            if res.error:
                return res
            return res.success(try_expr)
    
        if tok.matches(constants.KEYWORD, 'delete'):
            # del-expr ::= DELETE identifier
            res.register(self.advance())
            res.register_advancement()
            if self.current_token.type != constants.IDENTIFIER:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted an identifier'
                ))
            var_name = self.current_token
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.DeleteNode(var_name))
    
        if tok.matches(constants.KEYWORD, 'assert'):
            assert_expr = res.register(self.assert_expr())
            if res.error:
                return res
            return res.success(assert_expr)
    
        if tok.matches(constants.KEYWORD, 'switch'):
            switch_expr = res.register(self.switch_expr())
            if res.error:
                return res
            return res.success(switch_expr)
        
        if tok.matches(constants.KEYWORD, 'attr'):
            set_expr = res.register(self.set_expr())
            if res.error:
                return res
            return res.success(set_expr)
        
        if tok.matches(constants.KEYWORD, 'namespace'):
            namespace_expr = res.register(self.namespace_expr())
            if res.error:
                return res
            return res.success(namespace_expr)
        
        if tok.matches(constants.KEYWORD, 'using'):
            using_expr = res.register(self.using_expr())
            if res.error:
                return res
            return res.success(using_expr)
        
        left = res.register(self.comp_expr())
        if res.error:
            return res
        while (self.current_token.matches(constants.KEYWORD, 'and') or
               self.current_token.matches(constants.KEYWORD, 'or')):
            tok = self.current_token
            res.register(self.advance())
            res.register_advancement()
            right = res.register(self.comp_expr())
            if res.error:
                return res
            if tok.matches(constants.KEYWORD, 'and'):
                left = nodes.AndNode(left, right)
            else:
                left = nodes.OrNode(left, right)
                
        return res.success(left)
        
    def comp_expr(self):
        """
        comp-expr ::= term-expr ((LT | LTE | EE | NE | GT | GTE) term-expr)*
        """
        return self.bin_op(constants.OP_PRIORITY[0], self.term_expr)
    
    def term_expr(self):
        """
        term-expr ::= calc-expr ((PLUS | MINUS | AND | OR | XOR | LSHIFT | RSHIFT) calc-expr)*
        """
        return self.bin_op(constants.OP_PRIORITY[1], self.calc_expr)
    
    def calc_expr(self):
        """
        calc-expr ::= power-expr ((MUL | DIV | FLOOR | MOD | ARROW | QUESTION) power-expr)*
        """
        return self.bin_op(constants.OP_PRIORITY[2], self.power_expr)
    
    def power_expr(self):
        """
        power-expr ::= atom ((POW | DOUBLE) atom)*
        """
        return self.bin_op(constants.OP_PRIORITY[3], self.get_expr)
    
    def get_expr(self):
        res = ParserResult()
        cls = res.register(self.atom())
        if res.error:
            return res
        while self.current_token.type == constants.POINT:
            res.register(self.advance())
            res.register_advancement()
            attr = self.current_token
            if attr.type != constants.IDENTIFIER:
                return res.failure(errors.InvalidSyntaxError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    'excepted an identifier'
                ))
            res.register(self.advance())
            res.register_advancement()
            cls = nodes.AttrAccessNode(cls, attr)
        cls = res.register(self.index_or_call(cls))
        if res.error:
            return res
        return res.success(cls)
    
    def atom(self):
        """
        atom ::= factor [index-expr | call]
        """
        res = ParserResult()
        factor = res.register(self.factor())
        if res.error:
            return res
        atom = res.register(self.index_or_call(factor))
        if res.error:
            return res
        return res.success(atom)
    
    def index_or_call(self, factor):
        """
        index-or-call ::= ... [index-expr | call]
        """
        res = ParserResult()
        tok = self.current_token
        if tok.type == constants.LPAREN:
            call = res.register(self.call(factor))
            if res.error:
                return res
            return res.success(call)
        if tok.type == constants.LBRACKET:
            index_expr = res.register(self.index_expr(factor))
            if res.error:
                return res
            return res.success(index_expr)
        return res.success(factor)
        
    def bin_op(self, ops, func):
        """
        二元运算符通用构造函数
        func: 构造左右两边的语法函数
        """
        res = ParserResult()
        left = res.register(func())
        if res.error:
            return res
        while self.current_token.type in ops:
            tok = self.current_token
            res.register(self.advance())
            res.register_advancement()
            right = res.register(func())
            if res.error:
                return res
            left = nodes.BinaryOpNode(left, tok, right)
        return res.success(left)
    
    def parse(self):
        # 递归下降解析法入口
        res = self.program()
        if (not res.error) and self.current_token.type != constants.EOF:
            # 如果没有ERROR，但是没有遍历到末尾，仍然有语法错误
            # 类似于111 222这样的语句
            if res.error_token:
                self.current_token = res.error_token
            return ParserResult().failure(errors.InvalidSyntaxError(
                self.current_token.pos_start, self.current_token.pos_end,
                'this statement must not exist'
            ))
        return res
    
    def stmt(self):
        """
        stmt ::= return-expr | continue-expr | break-expr | PASS | expr
        """
        res = ParserResult()
        pos_start = self.current_token.pos_start.copy()
        if self.current_token.matches(constants.KEYWORD, 'pass'):
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.NullNode(self.current_token))
        if self.current_token.matches(constants.KEYWORD, 'return'):
            if not self.in_func:
                return res.failure(errors.OutsideError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    '"return" outside function'
                ))
            res.register(self.advance())
            res.register_advancement()
            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(nodes.ReturnNode(expr, pos_start, self.current_token.pos_end.copy()))
        if self.current_token.matches(constants.KEYWORD, 'continue'):
            if not self.in_loop:
                return res.failure(errors.OutsideError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    '"continue" outside loop'
                ))
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.ContinueNode(pos_start, self.current_token.pos_end.copy()))
        if self.current_token.matches(constants.KEYWORD, 'break'):
            if not self.in_loop:
                return res.failure(errors.OutsideError(
                    self.current_token.pos_start, self.current_token.pos_end,
                    '"break" outside loop'
                ))
            res.register(self.advance())
            res.register_advancement()
            return res.success(nodes.BreakNode(pos_start, self.current_token.pos_end.copy()))
        
        expr = res.register(self.expr())
        if res.error:
            return res
        return res.success(expr)
    
    def program(self):
        """
        blanks ::= (NEWLINE)*
        program ::= blanks (stmt blanks stmt)* blanks
        """
        res = ParserResult()
        pos_start = self.current_token.pos_start.copy()
        statements = []

        self.blanks(res)
        if self.current_token.type == constants.EOF:
            return res.success(nodes.ListNode(
                [], pos_start,
                self.current_token.pos_end.copy(),
                is_block=True,
            ))

        stmt = res.register(self.stmt())
        if res.error:
            return res
        statements.append(stmt)
        
        while True:
            if not self.blanks(res):
                break
                
            stmt = res.try_register(self.stmt())
            if not stmt:
                res.error_token = self.current_token
                # 有错误，下面可能是end一类的关键字，应该返回
                res.register(self.reverse(res.to_reverse_count))
                break
            statements.append(stmt)
            
        return res.success(nodes.ListNode(
            statements,
            pos_start,
            self.current_token.pos_end.copy(),
            is_block=True,
        ))
