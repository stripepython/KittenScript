from .. import constants, errors

def auto(value):
    if isinstance(value, Value):
        return value
    if isinstance(value, bool):
        return Bool(value)
    if value is None:
        return null.copy()
    if isinstance(value, str):
        return String(value)
    if isinstance(value, (int, float)):
        return Number(value)
    if isinstance(value, list):
        return List(value)
    if isinstance(value, dict):
        return Dict(value)
    return Value()


class Value(object):
    op_funcs = [
        'by_pos', 'by_neg', 'by_not', 'by_xat', 'by_invert', 'plus_by', 'minus_by',
        'mul_by', 'div_by', 'floor_by', 'index_by', 'arrow_by', 'ee_by', 'ne_by',
        'lt_by', 'lte_by', 'gt_by', 'gte_by', 'pow_by', 'question_by', 'xor_by',
        'lshift_by', 'rshift_by', 'and_by', 'or_by'
    ]
    
    def __init__(self):
        self.set_pos()
        self.set_context()
        self.attrs = {}

    def __str__(self):
        val = self.get()
        if val is None:
            return 'null'
        if val is True:
            return 'true'
        if val is False:
            return 'false'
        return str(val)

    def __repr__(self):
        val = self.get()
        if val is None:
            return 'null'
        if val is True:
            return 'true'
        if val is False:
            return 'false'
        return repr(val)
    
    def __eq__(self, other):
        return isinstance(other, Value) and self.get() == other.get()
    
    def __lt__(self, other):
        return isinstance(other, Value) and self.get() < other.get()
    
    def __gt__(self, other):
        return isinstance(other, Value) and self.get() > other.get()
    
    def __bool__(self):
        return self.is_true()
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def set_pos(self, pos_start=None, pos_end=None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self
    
    def is_true(self):
        return True
    
    def get(self):
        return NotImplemented
    
    def by_pos(self):
        return +(self.get()), None
    
    def by_neg(self):
        return -(self.get()), None
    
    def by_not(self):
        return not self.get(), None
    
    def by_xat(self):
        return id(self), None
    
    def by_invert(self):
        return ~(self.get()), None
    
    def plus_by(self, other):
        return self.get() + other.get(), None
    
    def minus_by(self, other):
        return self.get() - other.get(), None
    
    def mul_by(self, other):
        return self.get() * other.get(), None
    
    def div_by(self, other):
        return self.get() / other.get(), None
    
    def floor_by(self, other):
        return self.get() // other.get(), None
    
    def mod_by(self, other):
        return self.get() % other.get(), None
    
    def arrow_by(self, other):
        return self.get()[other.get()], None
    
    def pow_by(self, other):
        return self.get() ** other.get(), None
    
    def lt_by(self, other):
        return self.get() < other.get(), None
    
    def lte_by(self, other):
        return self.get() <= other.get(), None

    def ee_by(self, other):
        return self.get() == other.get(), None

    def ne_by(self, other):
        return self.get() != other.get(), None

    def gt_by(self, other):
        return self.get() > other.get(), None

    def gte_by(self, other):
        return self.get() >= other.get(), None
    
    def xor_by(self, other):
        return self.get() ^ other.get(), None
    
    def lshift_by(self, other):
        return self.get() << other.get(), None
    
    def rshift_by(self, other):
        return self.get() >> other.get(), None
    
    def question_by(self, other):
        return [self.get(), other.get()], None
    
    def and_by(self, other):
        return self.get() & other.get(), None
    
    def or_by(self, other):
        return self.get() | other.get(), None
    
    def at_by(self, other):
        ans = []
        for i in self.get():
            res = other.execute([i], None)
            if res.error:
                return None, res.error
            ans.append(res.value)
        return ans, None
    
    def execute(self, args, res):
        return res.failure(errors.FunctionError(
            self.pos_start, self.pos_end,
            'not a callable object', self.context
        ))
    
    def unary_op(self, op):
        try:
            if op == constants.PLUS:
                return self.by_pos()
            if op == constants.MINUS:
                return self.by_neg()
            if op == constants.NOT:
                return self.by_not()
            if op == constants.XAT:
                return self.by_xat()
            if op == constants.INVERT:
                return self.by_invert()
        except (Exception, SystemExit):
            return self.invalid(op, self, 'illegal operation')
        return self.invalid(op, self)
    
    def binary_op(self, op, other):
        if not isinstance(other, Value):
            return self.invalid(op, other)
        try:
            if op == constants.AND:
                return self.and_by(other)
            if op == constants.OR:
                return self.or_by(other)
            if op == constants.PLUS:
                return self.plus_by(other)
            if op == constants.MINUS:
                return self.minus_by(other)
            if op == constants.MUL:
                return self.mul_by(other)
            if op == constants.DIV:
                return self.div_by(other)
            if op == constants.FLOOR:
                return self.floor_by(other)
            if op == constants.MOD:
                return self.mod_by(other)
            if op == constants.POW:
                return self.pow_by(other)
            if op == constants.LT:
                return self.lt_by(other)
            if op == constants.LTE:
                return self.lte_by(other)
            if op == constants.EE:
                return self.ee_by(other)
            if op == constants.NE:
                return self.ne_by(other)
            if op == constants.GT:
                return self.gt_by(other)
            if op == constants.GTE:
                return self.gte_by(other)
            if op == constants.XOR:
                return self.xor_by(other)
            if op == constants.LSHIFT:
                return self.lshift_by(other)
            if op == constants.RSHIFT:
                return self.rshift_by(other)
            if op == constants.QUESTION:
                return self.question_by(other)
            if op == constants.DOUBLE:
                return other.contains(self)
            if op == constants.AT:
                return self.at_by(other)
        except (Exception, SystemExit):
            return self.invalid(op, other, f'illegal operation {op} for {self} and {other}')
        return self.invalid(op, other)
    
    def index_by(self, index):
        return self.invalid('GET-INDEX', index)
    
    def iter_by(self):
        return None, errors.MathError(
            self.pos_start, self.pos_end,
            'cannot become an iterable', self.context
        )
    
    def invalid(self, op, other, details=None):
        if details is None:
            details = f'invalid operation: {op} (for {self} and {other})'
        return None, errors.MathError(
            self.pos_start, other.pos_end,
            details, self.context
        )
    
    def contains(self, other):
        return self.invalid('CONTAIN', other)
    
    def getattr(self, name):
        attr = self.attrs.get(name, NotImplemented)
        if attr is NotImplemented:
            return None, errors.ClassError(
                self.pos_start, self.pos_end,
                f'no attribute named "{name}"', self.context
            )
        return attr, None
    
    def setattr(self, name, value):
        self.attrs[name] = value
        return null.copy(), None
    
    def set_attrs(self, attrs):
        self.attrs = attrs.copy()
        return self


class Single(Value):
    def __init__(self, value):
        self.value = value
        super().__init__()
    
    def copy(self):
        return (
            Single(self.value).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )
    
    def is_true(self):
        return bool(self.value)
    
    def get(self):
        return self.value
    
    
class Number(Single):
    def zero(self, other):
        return None, errors.MathError(other.pos_start, other.pos_end, 'division by zero', self.context)
    
    def div_by(self, other):
        if other.get() == 0:
            return self.zero(other)
        return super().div_by(other)
    
    def floor_by(self, other):
        if other.get() == 0:
            return self.zero(other)
        return super().floor_by(other)
    
    def mod_by(self, other):
        if other.get() == 0:
            return self.zero(other)
        return super().mod_by(other)
    
    def copy(self):
        return (
            Number(self.value).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )


class String(Single):
    def copy(self):
        return (
            String(self.value).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )

    def neg(self):
        return String(str(reversed(self.value))), None
    
    def div_by(self, other):
        return self.arrow_by(other)
    
    def index_by(self, index):
        return self.arrow_by(index)
    
    def contains(self, other):
        return Bool(auto(other) in self.value), None
    
    def invert(self):
        return String(''.join(reversed(self.value))), None
    
    def iter_by(self):
        return List([String(i) for i in self.value]), None


class Bool(Single):
    def copy(self):
        return (
            Bool(self.value).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )
    
    def invert(self):
        return Bool([True, False][self.value]), None


Bool.true = Bool(True)
Bool.false = Bool(False)
null = Single(None)


class List(Value):
    def __init__(self, items):
        super().__init__()
        self.items = items
    
    def __repr__(self):
        return self.items.__repr__()
    
    def get(self):
        return self.items
    
    def copy(self):
        return (
            List(self.items).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )
    
    def arrow_by(self, other):
        try:
            return self.items[other.get()], None
        except IndexError:
            return None, errors.ListError(
                other.pos_start, other.pos_end,
                'index out of range', self.context
            )
        except TypeError:
            return None, errors.ListError(
                other.pos_start, other.pos_end,
                f'{other.get()} cannot as index', self.context
            )

    def index_by(self, index):
        return self.arrow_by(index)
    
    def execute(self, args, res):
        try:
            val = [i.get() for i in args]
            for i in range(3 - len(val)):
                val.append(None)
            return res.success(List(self.items[val[0]:val[1]:val[2]]))
        except TypeError:
            return res.failure(errors.ListError(
                self.pos_start, self.pos_end,
                'slice indices must be integers', self.context
            ))
        except (Exception, SystemExit):
            return res.failure(self.invalid('SLICE', self)[1])
        
    def contains(self, other):
        return Bool(auto(other) in self.items), None
    
    def invert(self):
        return List(list(reversed(self.items))), None
    
    @staticmethod
    def is_array(arr):
        try:
            m = len(arr[0])
        except ValueError:
            return False
        for i in range(m):
            n = len(arr[1])
            if n != m:
                return False
        return True
    
    def iter_by(self):
        return self, None


class Dict(Value):
    def __init__(self, items):
        super().__init__()
        self.items = items
    
    def __repr__(self):
        return self.items.__repr__()
    
    def get(self):
        return self.items
    
    def copy(self):
        return (
            Dict(self.items).
            set_pos(self.pos_start, self.pos_end).
            set_context(self.context).
            set_attrs(self.attrs)
        )
    
    def or_by(self, other):
        if not isinstance(other, Dict):
            return None, errors.DictError(
                other.pos_start, other.pos_end,
                'not a dictionary', self.context
            )
        return Dict({**self.items, **other.items}), None
    
    def arrow_by(self, other):
        try:
            return self.items[other.get()], None
        except KeyError:
            return None, errors.DictError(
                other.pos_start, other.pos_end,
                f'key {other.get} not in dict', self.context
            )
        
    def index_by(self, index):
        return self.arrow_by(index)
    
    def contains(self, other):
        return Bool(other.get() in self.items), None
    
    def invert(self):
        return Dict({y.get(): auto(x) for x, y in self.items.items()}), None
    
    def iter_by(self):
        return List([List([auto(k), v]) for k, v in self.items.items()]), None
    
    
class Namespace(Value):
    def __init__(self, name):
        self.name = name
        super().__init__()
        
    def __repr__(self):
        return f'<namespace {self.name}>'
    
    def get(self):
        return self
    
    
class Printable(object):
    class TrueType(object):
        def __repr__(self):
            return 'true'
        
    class FalseType(object):
        def __repr__(self):
            return 'false'
        
    class NullType(object):
        def __repr__(self):
            return 'null'
        
    true = TrueType()
    false = FalseType()
    null = NullType()
