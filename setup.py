from setuptools import setup

setup(
    name='Biciklo',
    python_requires='>=3',
    version='1.1',
    packages=['biciklo'],
    entry_points={
        'console_scripts': ['biciklo-inventaire=biciklo.biciklo:main'],
    },
    install_requires=[
        'pymongo',
        'flask',
        'wtforms',
        'recherche_babac2',
    ],
    data_files=[
                ('.', ['config.yml.example'])
    ],
    zip_safe=False,
    include_package_data=True,
)
