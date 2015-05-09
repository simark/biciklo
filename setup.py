from setuptools import setup, find_packages

setup(
  name = 'Biciklo',
  version = '1.0',
  packages = find_packages(),
  entry_points = {
    'console_scripts': ['biciklo-inventaire=biciklo.biciklo:main'],
  },
  install_requires = [
    'pymongo',
    'flask',
  ]
)
