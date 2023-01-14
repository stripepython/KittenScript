import sys

from .src.basic import run
from .version import get_version


def use_interpreter(file, code, output_result, quit_if_error=True):
    try:
        result, error, ctx = run(file, code)
    except KeyboardInterrupt:
        print('KeyboardInterrupt')
        sys.exit()
    if error:
        print(error.as_string())
        if quit_if_error:
            sys.exit(1)
        return
    if output_result:
        for i in result.items:
            if i:
                print(i)
        

def interpreter_stdin():
    print(f'Welcome to KittenScript {get_version()}')
    while True:
        code = input('>>> ')
        use_interpreter('<stdin>', code, True, False)
        
        
def interpreter_file(path):
    try:
        io = open(path, 'r', encoding='utf-8')
    except (Exception, SystemExit) as e:
        print('Error:', e)
        sys.exit(1)
    code = io.read()
    io.close()
    use_interpreter(path, code, False)
        

if __name__ == '__main__':
    interpreter_stdin() if len(sys.argv) == 1 else interpreter_file(sys.argv[1])
