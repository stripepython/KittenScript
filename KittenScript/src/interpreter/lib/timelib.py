import time

def _time():
    return Number(time.time())


functions = {
    'time': PythonFunction(_time, 'time')
}
