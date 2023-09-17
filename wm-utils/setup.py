from setuptools import setup, find_packages

setup(
    name='wm-utils',
    version='0.0.2-dev',
    install_requires=[
        'requests>=2.31.0,<3.0',
        'redis[hiredis]>=4.6.0,<5.0',
    ],
    packages=find_packages(
        where='src'
    ),
    package_dir={
        '': 'src',
    },
)
