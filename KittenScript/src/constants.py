import string

DIGITS = set(string.digits + '.')
LETTERS = set(string.ascii_letters + '_$')
LETTERS_DIGITS = set(string.ascii_letters + string.digits + '_$')
NEWLINE_CHAR = {'\n', ';'}  # 换行字符
WHITESPACES = {'\t', ' ', ' ', '', ''}  # 忽略字符

PAREN_START = {'(', '[', '{'}
PAREN_END = {')', ']', '}'}

LPAREN = 'LPAREN'
RPAREN = 'RPAREN'
LBRACKET = 'LBRACKET'
RBRACKET = 'RBRACKET'
LBRACE = 'LBRACE'
RBRACE = 'RBRACE'

EOF = 'EOF'
NEWLINE = 'NEWLINE'
KEYWORD = 'KEYWORD'
IDENTIFIER = 'IDENTIFIER'

INT = 'INT'
FLOAT = 'FLOAT'
STRING = 'STRING'
BOOL = 'BOOL'
NULL = 'NULL'
LIST = 'LIST'
TYPES = {INT, FLOAT, STRING, BOOL, NULL}

PLUS = 'PLUS'
MINUS = 'MINUS'
MUL = 'MUL'
DIV = 'DIV'
FLOOR = 'FLOOR'
MOD = 'MOD'
POW = 'POW'

AND = 'AND'
OR = 'OR'
NOT = 'NOT'

EQ = 'EQ'  # =
LT = 'LT'  # <
GT = 'GT'  # >
EE = 'EE'  # ==
NE = 'NE'  # !=
LTE = 'LTE'  # <=
GTE = 'GTE'  # >=

COMMA = 'COMMA'  # ,
ARROW = 'ARROW'  # ->
XAT = 'XAT'  # *@
DOUBLE = 'DOUBLE'  # ::
# a :: b 即 b in a
POINT = 'POINT'  # .
AT = 'AT'  # @

XOR = 'XOR'
LSHIFT = 'LSHIFT'
RSHIFT = 'RSHIFT'
INVERT = 'INVERT'

QUESTION = 'QUESTION'
COLON = 'COLON'

# 内置函数列表
BUILTINS = ['__System_maxrecursion', '__System_maxsize', '__System_maxunicode', '__System_interpreter',
            '__System_platform', '__System_file', '__System_code', 'len', 'int', 'float', 'str',
            'string', 'list', 'range', 'append', 'clear', 'remove', 'print', 'printf', 'printe',
            'printp', 'input', 'enum', 'keys', 'values', 'items', 'getdefault', 'setdefault', 'ord',
            'char', 'poplist', 'popdict', 'getitem', 'setitem', 'delitem', 'typeof', 'sum', 'zip_short',
            'zip_long', 'replace', 'count', 'strip', 'lstrip', 'rstrip', 'split', 'slice',
            'counter', 'copy', 'deepcopy', 'join', 'find', 'index', 'startswith', 'endswith',
            'globals', 'system', 'bin', 'oct', 'hex', 'ellipsis', 'ternary', 'reverse', 'object',
            'sort', 'inf', 'nan', 'NotImplemented', 'defined_var', 'get_var']
KEYWORDS = {'true', 'false', 'null', 'for', 'while', 'to', 'var', 'if', 'elif', 'else',
            'step', 'exit', 'then', 'throw', 'function', 'include', 'do', 'end', 'return',
            'break', 'continue', 'try', 'catch', 'delete', 'lambda', 'assert', 'finally',
            'switch', 'case', 'default', 'and', 'or', 'not', 'pass', 'attr', 'namespace',
            'using', 'unless'}  # 关键字集合
SPECIAL_KEYWORDS = {
    'true': (BOOL, True),
    'false': (BOOL, False),
    'null': (NULL, None),
}

OP_DICT = {
    '+': (PLUS, {}),
    '-': (MINUS, {'>': ARROW}),
    '*': (MUL, {'*': POW, '@': XAT}),
    '/': (DIV, {'/': FLOOR}),
    '&': (AND, {}),
    '|': (OR, {}),
    '!': (NOT, {'=': NE}),
    '=': (EQ, {'=': EE}),
    '<': (LT, {'=': LTE, '<': LSHIFT, '>': NE}),
    '>': (GT, {'=': GTE, '>': RSHIFT}),
    '%': (MOD, {}),
    '?': (QUESTION, {}),
    ':': (COLON, {':': DOUBLE}),
    '(': (LPAREN, {}),
    ')': (RPAREN, {}),
    '{': (LBRACE, {}),
    '}': (RBRACE, {}),
    ',': (COMMA, {}),
    '[': (LBRACKET, {}),
    ']': (RBRACKET, {}),
    '^': (XOR, {}),
    '~': (INVERT, {}),
    '.': (POINT, {}),
    '@': (AT, {}),
}  # 分隔符表
OP_REDICT = {
    PLUS: '+', MINUS: '-', MUL: '*', DIV: '/', FLOOR: '//', MOD: '%', INVERT: '~', XOR: '^',
    AND: '&', OR: '|', NOT: 'not ', LT: '<', LTE: '<=', EE: '==', NE: '!=', GT: '>', GTE: '>=',
    DOUBLE: ' in ', LSHIFT: '<<', RSHIFT: '>>'
}
OP_PRIORITY = (
    {LT, LTE, EE, NE, GT, GTE},
    {PLUS, MINUS, AND, OR, XOR, LSHIFT, RSHIFT},
    {AT, MUL, DIV, FLOOR, MOD, ARROW, QUESTION},
    {POW, DOUBLE},
)  # 运算符优先级四元组
BINARY_OP = {
    LT, LTE, EE, NE, GT, GTE, PLUS, MINUS,
    AND, OR, MUL, DIV, FLOOR, MOD, ARROW, POW,
    DOUBLE, LSHIFT, RSHIFT, XOR,
}  # 所有二元运算符
MATH_BINARY_OP = {
    PLUS, MINUS, AND, OR, MUL, DIV, FLOOR, MOD, POW, XOR, LSHIFT, RSHIFT,
}  # 所有算术二元运算符
UNARY_OP = {PLUS, MINUS, NOT, XAT, INVERT}  # 所有一元运算符

ESCAPE_CHARACTERS = {
    'n': '\n',
    'r': '\r',
    'a': '\a',
    'b': '\b',
    't': '\t',
    'f': '\f',
    'v': '\v',
    '0': '\0',
}  # 转义字符表

PYTHON_MODULE = {'.py', '.py3', '.pyw', '.pym', '.pyks'}  # 所有支持的python模块扩展名

MAX_RECURSION = 2 ** 26 - 1
