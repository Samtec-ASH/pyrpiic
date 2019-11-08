import io
import re

from setuptools import find_packages, setup

with open('README.md', 'r') as fp:
    long_description = fp.read()

with io.open("pyrpiic/__init__.py", "rt", encoding="utf8") as fp:
    version = re.search(r'__version__ = "(.*?)"', fp.read()).group(1)
    (major_version, minor_version, revision) = version.split('.')

setup(
    name='PyRPIIC',
    version=version,
    description='Python RPI interface to low-level ICs',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Samtec - ASH',
    author_email='samtec-ash@samtec.com',
    url='https://github.com/Samtec-ASH/pyrpiic',
    packages=find_packages(),
    python_requires='>=3.6'
)
