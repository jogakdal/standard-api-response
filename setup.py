from setuptools import setup, find_packages

with open("readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='standard-api-response',
    version='1.3.6',
    author='황용호',
    author_email='jogakdal@gmail.com',
    description='Standard API response helper package',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/jogakdal/standard-api-response',
    install_requires=['fastapi', 'inflection', 'convertable-key-model'],
    packages=find_packages(exclude=['service', 'tests']),
    keywords=['jogakdal', 'standard', 'API', 'response', 'helper', 'pydantic'],
    python_requires='>=3.6',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)
