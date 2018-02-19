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
    url="https://github.com/Julian/Minion",
    description="A microframework based on evil intentions and "
                "whatever else you've got",
    license="MIT",
    classifiers=classifiers,
    long_description=long_description,

    author="Julian Berman",
    author_email="Julian@GrayVines.com",

    packages=find_packages(),

    setup_requires=["setuptools_scm"],
    use_scm_version=True,

    install_requires=[
        "attrs",
        "cached-property",
        "future",
        "itsdangerous",
        "pyrsistent",
        "Werkzeug",
    ],
)
