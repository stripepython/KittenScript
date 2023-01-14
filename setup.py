from setuptools import setup, find_packages

from KittenScript.version import get_version

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='opengame',
    packages=find_packages(where='.', exclude=(), include=('*',)),
    author='stripe-python',
    author_email='stripe-python@139.com',
    maintainer='stripe-python',
    maintainer_email='stripe-python@139.com',
    license='MIT License',
    install_requires=['click'],
    version=get_version(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/stripepython/KittenScript/',
)
