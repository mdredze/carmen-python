from setuptools import setup, find_packages

setup(
    name='carmen',
    version='0.0.3',
    description='Geolocation for Twitter',
    author='Roger Que',
    author_email='query@jhu.edu',
    url='https://github.com/query/carmen',
    packages=find_packages(),
    package_data={'carmen': ['data/*']},
    install_requires=['geopy'],
    license='2-clause BSD',
    zip_safe=True)
