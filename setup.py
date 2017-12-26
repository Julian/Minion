import os

from setuptools import find_packages, setup


with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

setup(
    name="minion",
    packages=find_packages(),
    setup_requires=["vcversioner"],
    install_requires=[
        "attrs",
        "cached-property",
        "future",
        "itsdangerous",
        "pyrsistent",
        "Werkzeug",
    ],
    author="Julian Berman",
    author_email="Julian@GrayVines.com",
    classifiers=classifiers,
    license="MIT",
    long_description=long_description,
    url="https://github.com/Julian/Minion",
    description="A microframework based on evil intentions and "
                "whatever else you've got",
    vcversioner={"version_module_paths" : ["minion/_version.py"]},
)
