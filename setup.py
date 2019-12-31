from setuptools import setup

setup(
    name='Biciklo',
    version='1.0',
    packages=['biciklo'],
    entry_points={
        'console_scripts': ['biciklo-inventaire=biciklo.biciklo:main'],
    },
    install_requires=[
        'pymongo',
        'flask',
        'wtforms',
        'requests',
        'bs4',
        'pyyaml',
        'lxml',
    ],
    zip_safe=False,
    include_package_data=True,
)
