# KittenScript
`KittenScript` is a high-level explanatory programming language written in `python3.7`.

Block in `KittenScript` like `lua`.

# Install
First, you need `python>=3.6` and `pip` or `git`.  
Then, use `pip` or `git` install it:

Use `pip`:
```shell
pip install -U KittenScript
```

Use `git`:
```shell
git clone https://github.com/stripepython/KittenScript/
cd KittenScript
pip install -r requirements.txt
python setup.py install
```

Test if installed well:
```shell
python -m KittenScript -v
```

# Run
Use `KittenScript/__main__.py`.

Usage: `python -m KittenScript [OPTIONS] FILE`

Options:    
```
-v, --version  Show the version and exit.    
-i, --ide      Show the IDE in English and exit.    
-ic, --ide-cn  Show the IDE in Chinese and exit.   
-s, --stdio    Enter interactive programming.    
--help         Show this message and exit.    
```

And use `python -m KittenScript FILE` to run file.  
Like this:
```shell
python -m KittenScript test.kst
```

# Basic grammar

## Arithmeter

Same as all mainstream programming languages:

For example:
```python
1 + 1
(2 + 3) * 4
7 + 6 * 5 > 2 == true
```

## Booleans
Two keywords: `true` and `false`.

## Lists
For lists, `KittenScript` is the same as Python:
```python
[]
[1, 2, 3]
[1, "2", true]  # Support different types
[[1, 2, 3], [4, 5, 6]]   # 2D List
[[[1, 2], [3, 4]], [[5, 6], [7, 8]]]  # 3D List
# Can wrap
[
    "apple",
    "banana",
    "strawberry",
    "watermelon"
]
```

## Dictionaries(Dict)
For dictionaries, `KittenScript` is the same as Python too:

```python 
{}
{'first': 1, 'second': 2}
# Can wrap
{
    'perfect': 2,
    'good': 1,
    'bad': 0
} 
```

## Strings
For strings, `KittenScript` is similar to `python2`.
You can use `"`, `'` or "`".

```python
''
"12345"
'Hello, World!'
`\n`  # Likes "\\n"

"Test\nTest\t"
'\''
```

## Variables

Use `var` keyword to define a variable:
```python
var a = 1
var b = 0.3 + 9.0
var c = var d = [1, 2]
```

If you use `CONST_` prefix, it will be a const variable.  
When the const variable is defined in this namespace, you can't redefine it.
```python
var CONST_PI = 3.14

var CONST_PI = 3.1415926  # Error!
```

You can use `+=`, `-=` and things like that too:
```python 
var a = 65535
var a += 1   # Must define a first!
var a >>= 1

var b ^= 3  # Error: b is not defined
```

## Flow Of Control

### If-elif-else

Oneline(Ternary expression)：
```python
if true then 1  # else null
if null then 0 else 1   # Ternary expression
if false then 1 elif 0 then 2 elif null then 3 else 4
```

Multi-line:
```python
if 1 then
    print("1 is true")
end

if 0 then
    print("0 is true")
else
    print("0 is false")
end

if 0 then
    print("0 is true")
elif 1 then
    print("0 is false and 1 is true")
else
    print("0 and 1 are false")
end

```

### While-else
Oneline (List comprehension and you cannot use else):

```python
var a = 0
var arr = while a < 10 var a += 1
# [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```

And multi-line:

```python 
var a = 0
while a < 10 then
    print(a)
    var a += 1
end
```

`Else` statement is like Python.  

It refers to the code to be executed after the normal end of the loop, 
that is, if the loop is terminated by the `break`, 
the indented code under else will not be executed.

```python 
var a = 0
while a < 10 then
    print(a)
    var a += 1
    if a > 5 then break
else
    print("Else")  # will not be executed
end
```

You can use break and continue like other high-level programming languages:

```python 
var a = -1
while a < 10 then
    var a += 1
    if a % 2 == 0 then continue
    if a > 7 then break
    print(a)
end
```

This is equivalent to:

```python 
var a = -1
while a < 10 then
    var a += 1
    if a % 2 == 0 then 
        continue
    end
    if a > 7 then 
        break
    end
    print(a)
end
```

### For-else
It's like while-else expr.

Usage:
```python 
for i = start_value(default is 0) to end_value step step_value(default is 1) then
    ...
end
```

Like this in Python:
```python 
for i in range(start_value, end_value, step_value):
    ...
```

Oneline:
```python
var arr = for i to 5 then i ** 2  # [0, 1, 4, 9, 16]
```

If you want to traverse a list, you can write like this:
```python
var arr = [1, 2, 9, 3, 15, -6, 28, 1, 7]
for i to len(arr) then
    print(arr[i])
end
```

And an example (use `else`) is as follows:
```python 
var sentence = ['an', 'apple', 'a', 'day']
for i to len(sentence) then
    if arr[i] == 'banana' then break
else
    print('No bananas!')
```

### Try-catch-else-finally
If you want to catch errors, you can:
```python
try 
    1 / 0
catch error, details then
    ...
end
```

Oneline (An expression):

```python
try 1 / 0 catch error, details then error + ':' + details
```

And multi-line:

```python
try 
    1 / 0
catch error, details then
    ...
else
    ...
finally
    ...
end
```

This likes Python.

## Include
The keyword `include` is like `c`:

```python
include "math.kst"
```

Or you can:
```python
include "math"
```

It can import from `/KittenScript/src/interpreter/lib` or CWD.

Using `KittenScript` to write modules is easy. You just need write a `KittenScript` program and include it:

```python
# target.kst
var pi = 3.1416
var e = 2.71828
```

```python
# main.kst
include "target.kst"
print(pi, e)
```

And you can use `Python3` too. But it's difficult. (Even you can use `c` or `c++`!)

## Functions
Use `function` or `lambda`.  
Default parameters and variable length parameters are temporarily not supported.

Oneline:
```python
function max(a, b) do if a >= b then a else b
var max = lambda a, b do if a >= b then a else b
```

Multi-line:
```python
function fib(n)
    if n == 1 then return 1
    if n == 2 then return 1
    return fib(n - 1) + fib(n - 2)
end
```

`return` is same as all high-level programming languages.

## Namespace
You can use `namespace` keyword to create a namespace.

This is from `heap.kst` from STL:

```python
namespace Heap
    function empty(arr) do len(arr) == 0

    function top(arr)
        if Heap.empty(arr) then throw "MathError", "empty heap"
        return arr[0]
    end

    function siftup(arr, e, last)
        var i = last
        var j = (last - 1) // 2
        while i > 0 and e < arr[j] then
            setitem(arr, i, arr[j])
            var i = j
            var j = (j - 1) // 2
        end
        setitem(arr, i, e)
    end

    function push(arr, e)
        append(arr, null)
        Heap.siftup(arr, e, len(arr) - 1)
    end

    function siftdown(arr, e, begin, end_)
        var i = begin
        var j = begin * 2 + 1
        while j < end_ then
            if j + 1 < end_ and arr[j + 1] < arr[j] then var j = j + 1
            if e < arr[j] then break
            setitem(arr, i, arr[j])
            var i = j
            var j = 2 * j + 1
        end
        setitem(arr, i, e)
    end

    function pop(arr)
        if Heap.empty(arr) then throw "MathError", "empty heap"
        var e0 = arr[0]
        var e = poplist(arr)
        if len(arr) > 0 then Heap.siftdown(arr, e, 0, len(arr))
        return e0
    end

    function heapify(arr)
        var end_ = len(arr)
        for i = end_ // 2 - 1 to -1 step -1 then
            Heap.siftdown(arr, arr[i], i, end_)
        end
    end
end

using Heap.*

```

You can use `using` to use the function.

```python
using Heap.heapify   # Only use heapify
using Heap.*  # All
```

# Some Examples

## Fibonacci
```python
function fib(n)
    if n == 1 then return 1
    if n == 2 then return 1
    return fib(n - 1) + fib(n - 2)
end
print(fib(15))
```

## Quick Sort
```python
function _partition(arr, left, right, cmp)
    var tmp = arr[left]
    while left < right then
        while left < right and cmp(tmp, arr[right]) then
            var right = right - 1
        end
        setitem(arr, left, arr[right])
        while left < right and cmp(arr[left], tmp) then
            var left = left + 1
        end
        setitem(arr, right, arr[left])
    end    
    setitem(arr, left, tmp)
    return left
end

function _quick_sort(arr, left, right, cmp)
    var mid = _partition(arr, left, right, cmp)
    _quick_sort(arr, left, mid - 1, cmp)
    _quick_sort(arr, mid + 1, right, cmp)
end

function qsort(array, cmp) do _quick_sort(array, 0, len(array) - 1, cmp)  # Quick Sort
```

# Floor Div
```python
function floor(dividend, divisor)
    if divisor == 0 then throw "MathError", "division by zero"

    var rev = false
    if dividend > 0 then
        var dividend = -dividend
  	    var rev = not rev
    end
    if divisor > 0 then
        var divisor = -divisor
        var rev = not rev
    end
    var candidates = [divisor]
    
    while candidates[-1] >= dividend - candidates[-1] then
        append(candidates, candidates[-1] + candidates[-1])
    end
    
    var ans = 0
    for i = len(candidates) - 1 to -1 step -1 then
        if candidates[i] >= dividend then
            var ans = ans + (1 << i)
            var dividend = dividend - candidates[i]
        end
    end
    
    return if rev then -ans else ans
end
```
