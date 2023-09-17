from setuptools import setup, find_packages

setup(
    name='wm-utils',
    version='0.0.1',
    install_requires=[
        'requests==2.31.0'
    ],
    packages=find_packages(
        where='src'
    ),
    package_dir={
        '': 'src',
    },
)
