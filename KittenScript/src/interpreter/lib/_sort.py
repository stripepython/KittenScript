def defined_sort(array, key):
    assert isinstance(array, List), 'must be a list'
    assert isinstance(key, Function), 'must be a function'
    
    def _key(x):
        res = key.execute([x], RTResult())
        if res.error:
            raise Exception(res.error.details)
        return res.value.get()
    
    array.items.sort(key=_key)
    return null.copy()


functions['defined_sort'] = PythonFunction(defined_sort, 'defined_sort')
