import math
import sys
import copy
import json
from os import system, mkdir
from os.path import exists
from pprint import pprint
from collections import Counter
from itertools import zip_longest

from . import constants
from .lexer.lexer import Lexer
from .parse.parser import Parser
from .interpreter.values import String, Number, Single, Printable
from .interpreter.interpreter import Interpreter, BuiltInFunction
from .interpreter.context import Context
from .interpreter.table import SymbolTable

global_symbol_table = SymbolTable()

sys.setrecursionlimit(constants.MAX_RECURSION)
global_symbol_table.set('__System_maxrecursion', Number(constants.MAX_RECURSION))
global_symbol_table.set('__System_maxsize', Number(sys.maxsize))
global_symbol_table.set('__System_maxunicode', Number(sys.maxunicode))
global_symbol_table.set('__System_interpreter', String(__file__))
global_symbol_table.set('__System_platform', String(sys.platform))

def set_builtins():
    def read(file, encoding='utf-8'):
        with open(file, 'r', encoding=encoding) as f:
            res = f.read()
        return res
    
    def write(file, content, encoding='utf-8'):
        with open(file, 'w', encoding=encoding) as f:
            f.write(content)
    
    global_symbol_table.set('defined_var', BuiltInFunction(lambda x: x in global_symbol_table.symbols, 'defined_var'))
    global_symbol_table.set('get_var', BuiltInFunction(lambda *args: global_symbol_table.symbols.get(args), 'get_var'))
    
    global_symbol_table.set('ellipsis', Single(...))
    global_symbol_table.set('NotImplemented', Single(NotImplemented))
    global_symbol_table.set('nan', Number(math.nan))
    global_symbol_table.set('inf', Number(math.inf))
    
    global_symbol_table.set('len', BuiltInFunction(len, 'len'))
    global_symbol_table.set('int', BuiltInFunction(int, 'int'))
    global_symbol_table.set('float', BuiltInFunction(float, 'float'))
    global_symbol_table.set('str', BuiltInFunction(str, 'str'))
    global_symbol_table.set('string', BuiltInFunction(repr, 'string'))
    global_symbol_table.set('list', BuiltInFunction(list, 'list'))
    global_symbol_table.set('range', BuiltInFunction(lambda *args: list(range(*args)), 'range'))
    global_symbol_table.set('append', BuiltInFunction(lambda x, y: x.append(y), 'append'))
    global_symbol_table.set('remove', BuiltInFunction(lambda x, y: x.remove(y), 'remove'))
    global_symbol_table.set('clear', BuiltInFunction(lambda x: x.clear(), 'clear'))
    global_symbol_table.set('reverse', BuiltInFunction(lambda x: list(reversed(x)), 'reverse'))
    global_symbol_table.set('extend', BuiltInFunction(lambda x, y: x.extend(y), 'extend'))
    
    global_symbol_table.set('enum', BuiltInFunction(
        lambda x, y=0: [[i, j] for i, j in enumerate(x, y)], 'enum'
    ))
    
    global_symbol_table.set('keys', BuiltInFunction(lambda x: list(x.keys()), 'keys'))
    global_symbol_table.set('values', BuiltInFunction(lambda x: list(x.values), 'values'))
    global_symbol_table.set('items', BuiltInFunction(lambda x: [[i, j] for i, j in x.items()], 'items'))
    global_symbol_table.set('getdefault', BuiltInFunction(
        lambda x, key, default=None: x.get(key, default), 'getdefault'
    ))
    global_symbol_table.set('setdefault', BuiltInFunction(
        lambda x, key, default=None: x.setdefault(key, default), 'setdefault'
    ))
    
    global_symbol_table.set('ord', BuiltInFunction(ord, 'ord'))
    global_symbol_table.set('char', BuiltInFunction(chr, 'char'))
    
    global_symbol_table.set('poplist', BuiltInFunction(lambda x, y=-1: x.pop(y), 'poplist'))
    global_symbol_table.set('popdict', BuiltInFunction(lambda x, y: x.pop(y), 'popdict'))
    global_symbol_table.set('getitem', BuiltInFunction(lambda x, y: x[y], 'getitem'))
    global_symbol_table.set('setitem', BuiltInFunction(
        lambda x, key, value: x.__setitem__(key, value), 'setitem'
    ))
    global_symbol_table.set('delitem', BuiltInFunction(
        lambda x, key: x.__delitem__(key), 'delitem'
    ))
    global_symbol_table.set('typeof', BuiltInFunction(lambda x: type(x).__name__, 'typeof'))
    global_symbol_table.set('sum', BuiltInFunction(lambda x: sum(x), 'sum'))
    global_symbol_table.set('zip_short', BuiltInFunction(
        lambda *args: [list(i) for i in zip(*args)], 'zip_short'
    ))
    global_symbol_table.set('zip_long', BuiltInFunction(
        lambda *args: [list(i) for i in zip_longest(*args)], 'zip_long'
    ))
    
    global_symbol_table.set('replace', BuiltInFunction(lambda x, y, z='': x.replace(y, z), 'replace'))
    global_symbol_table.set('count', BuiltInFunction(lambda x, y: x.count(y), 'count'))
    global_symbol_table.set('strip', BuiltInFunction(lambda x, y=' ': x.strip(y), 'strip'))
    global_symbol_table.set('lstrip', BuiltInFunction(lambda x, y=' ': x.lstrip(y), 'lstrip'))
    global_symbol_table.set('rstrip', BuiltInFunction(lambda x, y=' ': x.rstrip(y), 'rstrip'))
    global_symbol_table.set('split', BuiltInFunction(lambda x, y=' ': x.split(y), 'split'))
    global_symbol_table.set('slice', BuiltInFunction(
        lambda x, start=None, stop=None, step=None: x[start:stop:step], 'slice'
    ))
    global_symbol_table.set('counter', BuiltInFunction(lambda x: dict(Counter(x)), 'counter'))
   
    global_symbol_table.set('copy', BuiltInFunction(copy.copy, 'copy'))
    global_symbol_table.set('deepcopy', BuiltInFunction(copy.deepcopy, 'deepcopy'))
    global_symbol_table.set('join', BuiltInFunction(lambda x, y: y.join(x), 'join'))
    global_symbol_table.set('find', BuiltInFunction(lambda x, y: x.find(y), 'find'))
    global_symbol_table.set('index', BuiltInFunction(lambda x, y: x.index(y), 'index'))
    global_symbol_table.set('startswith', BuiltInFunction(lambda x, y: x.startswith(y), 'startswith'))
    global_symbol_table.set('endswith', BuiltInFunction(lambda x, y: x.endswith(y), 'endswith'))
    
    global_symbol_table.set('bin', BuiltInFunction(lambda x: bin(x).replace('0b', ''), 'bin'))
    global_symbol_table.set('oct', BuiltInFunction(lambda x: oct(x).replace('0o', ''), 'oct'))
    global_symbol_table.set('hex', BuiltInFunction(lambda x: hex(x).replace('0x', ''), 'hex'))
    
    global_symbol_table.set('ternary', BuiltInFunction(lambda a, b, c: b if a else c, 'ternary'))
    
    global_symbol_table.set('read', BuiltInFunction(read, 'read'))
    global_symbol_table.set('write', BuiltInFunction(write, 'write'))
    
    global_symbol_table.set('globals', BuiltInFunction(lambda: global_symbol_table.symbols, 'globals'))
    global_symbol_table.set('system', BuiltInFunction(lambda cmd: system(cmd), 'system'))

    global_symbol_table.set('sort', BuiltInFunction(lambda x: x.sort(), 'sort'))


def filter_args(args):
    res = []
    for i in args:
        if i is True:
            res.append(Printable.true)
        elif i is False:
            res.append(Printable.false)
        elif i is None:
            res.append(Printable.null)
        else:
            res.append(i)
    return res


set_builtins()

def run(file, text, out_io=sys.stdout):
    global_symbol_table.set('print', BuiltInFunction(
        lambda *args: print(*filter_args(args), file=out_io), 'print'
    ))
    global_symbol_table.set('printf', BuiltInFunction(
        lambda *args: print(*filter_args(args), end='', file=out_io), 'printf'
    ))
    global_symbol_table.set('printe', BuiltInFunction(
        lambda value, end: print(*filter_args([value]), end=end, file=out_io), 'printe'
    ))
    global_symbol_table.set('printp', BuiltInFunction(
        lambda *args: pprint(*filter_args(args), stream=out_io), 'printp'
    ))
    global_symbol_table.set('input', BuiltInFunction(input, 'input'))
    
    global_symbol_table.set('__System_file', String(file))
    global_symbol_table.set('__System_code', String(text))
    
    lexer = Lexer(file, text)
    tokens, error = lexer.make_tokens()  # 词法解析
    # print(tokens)
    if error:
        return None, error, None
    if not exists('.parse'):
        mkdir('.parse')
    with open('.parse/tokens.json', 'w', encoding='utf-8') as fp:
        json.dump([tok.as_json() for tok in tokens], fp, skipkeys=True, ensure_ascii=True, indent=4, sort_keys=True)
    
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error:
        return None, ast.error, None
    with open('.parse/ast.json', 'w', encoding='utf-8') as fp:
        json.dump(ast.node.as_json(), fp, skipkeys=True, ensure_ascii=False, indent=4, sort_keys=True)
    interpreter = Interpreter()
    context = Context('<program>')
    context.symbol_table = global_symbol_table
    interpreter.run_func = run
    res = interpreter.visit(ast.node, context)
    
    return res.value, res.error, context
