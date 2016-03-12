from setuptools import setup

VERSION = '0.9.0'

setup(
    name='anatomy_tagging',
    version=VERSION,
    description='Application for tagging svg images for anatomy practice app',
    author='Vit Stanislav',
    author_email='slaweet@seznam.cz',
    namespace_packages=[],
    include_package_data=True,
    packages=[
    ],
    install_requires=[
        'Django>=1.7,<1.8',
        'clint',
        'wikipedia',
        'beautifulsoup4',
    ],
    license='Gnu GPL v3',
)
