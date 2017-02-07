from setuptools import setup
import io
import re
import os

__author__ = 'Cedric Zhuang'


def version():
    desc = get_long_description()
    ret = re.findall(r'VERSION: (.*)', desc)[0]
    return ret.strip()


def here(filename=None):
    ret = os.path.abspath(os.path.dirname(__file__))
    if filename is not None:
        ret = os.path.join(ret, filename)
    return ret


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n\n')
    buf = []
    for filename in filenames:
        with io.open(here(filename), encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


def get_long_description():
    filename = 'README.rst'
    return read(filename)


setup(
    name="cachez",
    version=version(),
    author="Cedric Zhuang",
    author_email="jealous@163.com",
    description="Cache decorator for global or instance level memoize.",
    license="Apache Software License",
    keywords="cache decorator",
    url="http://github.com/jealous/cachez",
    py_modules=['cachez', 'cachez_test'],
    platforms=['any'],
    long_description=get_long_description(),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Natural Language :: English",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=read_requirements('requirements.txt'),
    tests_require=read_requirements('test-requirements.txt')
)
