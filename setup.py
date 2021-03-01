import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="husqvarna_automower",
    version="2021.2.3",
    author="Thomas Protzner",
    author_email="thomas.protzner@gmail.com",
    description="module to communicate to Husqvarna Automower API",
    license="Apache License 2.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Thomas55555/husqvarna_automower_py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=list(val.strip() for val in open("requirements.txt")),
)
