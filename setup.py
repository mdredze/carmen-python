from setuptools import setup, find_packages

setup(
    name='carmen',
    version='0.0.1',
    description='Geolocation for Twitter',
    author='Roger Que',
    author_email='query@jhu.edu',
    url='https://github.com/query/carmen',
    packages=find_packages(),
    install_requires=['geopy'],
    license='2-clause BSD')
