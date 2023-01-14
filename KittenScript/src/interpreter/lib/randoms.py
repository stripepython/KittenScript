import uuid
import random
import secrets

def _seed(x):
    random.seed(x.get())
    return null.copy()

def _shuffle(lst):
    random.shuffle(lst.get())
    return null.copy()


f = PythonFunction
functions = {
    'random': f(lambda: Number(random.random()), 'random'),
    'randint': f(lambda x, y: Number(random.randint(x.get(), y.get())), 'randint'),
    'uniform': f(lambda x, y: Number(random.uniform(x.get(), y.get())), 'uniform'),
    'choice': f(lambda lst: auto(random.choice(lst.get())), 'choice'),
    'seed': f(_seed, 'seed'),
    'shuffle': f(_shuffle, 'shuffle'),
    'really_choice': f(lambda lst: auto(secrets.choice(lst.get())), 'really_choice'),
    'randuuid': f(lambda: String(uuid.uuid1().hex), 'randuuid')
}
