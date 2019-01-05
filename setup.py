# -*- coding: utf-8 -*-
import ast
import os
import re

from setuptools import find_packages, setup

# parse version from apirun/__init__.py
_version_re = re.compile(r'__version__\s+=\s+(.*)')
_init_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "apirun", "__init__.py")
with open(_init_file, 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='apirun',
    version=version,
    description="API testing framework",
    long_description="""APIRun is a python utility for doing easy API test.""",
    classifiers=[
        "Topic :: API test",
        "Development Status :: 1 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
    ],
    keywords='',
    author='Guo Tengda',
    author_email='',
    url='',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=False,
    install_requires=["requests>=2.9.1", "ddt>=1.2.0", "xlrd>=1.2.0"],
    test_suite="",
    tests_require=[],
    entry_points={
        'console_scripts': [
            'apirun = apirun.main:main',
        ]
    },
)
