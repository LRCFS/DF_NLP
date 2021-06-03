from setuptools import setup, find_packages

with open("README.md") as f:
    readme = f.read()

with open("LICENSE") as f:
    license = f.read()

setup(
    name="DF_NLP",
    version="0.0.0",
    description="Grouping of scripts related to digital forensics NLP",
    long_description=readme,
    author="Maël LE GALL",
    author_email="mael.le_gall@tutanota.com",
    url="https://github.com/legallm/DF_NLP",
    license=license,
    packages=find_packages()
)
