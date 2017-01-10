from setuptools import setup, find_packages

setup(
    name='carmen',
    version='0.0.4',
    description='Geolocation for Twitter',
    author='Roger Que and Mark Dredze',
    author_email='mark@dredze.com',
    url='https://github.com/mdredze/carmen-python',
    packages=find_packages(),
    package_data={'carmen': ['data/*']},
    install_requires=['geopy'],
    license='2-clause BSD',
    zip_safe=True)
