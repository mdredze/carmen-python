from setuptools import setup, find_packages

setup(
    name='carmen',
    version='2.0.0',
    description='Geolocation for Twitter',
    author='Jack Jingyu Zhang, Alexandra DeLucia, Roger Que, and Mark Dredze',
    author_email='mark@dredze.com',
    url='https://github.com/mdredze/carmen-python',
    packages=find_packages(),
    package_data={'carmen': ['data/*']},
    install_requires=[
        'geopy>=1.11.0',
        'jsonlines>=3.1.0',
    ],
    license='2-clause BSD',
    zip_safe=True)
