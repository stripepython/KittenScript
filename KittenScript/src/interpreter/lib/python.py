def _eval(string):
    namespace = {}
    eval(string.get(), namespace)
    return Dict({key: auto(value) for key, value in namespace.items()})


def _exec(string):
    namespace = {}
    exec(string.get(), namespace)
    return Dict({key: auto(value) for key, value in namespace.items()})


functions = {
    'eval': PythonFunction(_eval, 'eval'),
    'exec': PythonFunction(_exec, 'exec'),
}
