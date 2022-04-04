import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aioautomower",
    author="Thomas Protzner",
    author_email="thomas.protzner@gmail.com",
    description="module to communicate to Husqvarna Automower API",
    license="Apache License 2.0",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Thomas55555/aioautomower",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    install_requires=list(val.strip() for val in open("requirements.txt")),
    version="2022.4.2",
    entry_points={
        "console_scripts": ["automower=aioautomower.cli:main"],
    },
)
