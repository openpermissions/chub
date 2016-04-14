
from setuptools import setup
import re

with open('chub/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

setup(name='chub',
      version=version,
      description='Asynchronous Python client for the Open Permissions Platform Coalition REST Services',
      author='Open Permissions Platform Coalition',
      author_email='support-copyrighthub@cde.catapult.org.uk',
      url='https://github.com/openpermissions/chub',
      packages=['chub'],
      install_requires=['tornado'])
