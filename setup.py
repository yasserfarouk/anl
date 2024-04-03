#!/usr/bin/env python

import re
from glob import glob
from os.path import basename, dirname, join, splitext

from setuptools import find_packages, setup


def read(*names, **kwargs):
    with open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


setup(
    name="anl",
    version="0.1.10",
    description="ANAC Automated Negotiations League Platform",
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    long_description_content_type="text/x-rst",  # Optional (see note above),
    author="Yasser Mohammad",
    author_email="yasserfarouk@gmail.com",
    url="https://github.com/autoneg/anl",
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        # 'Topic :: Utilities',
    ],
    project_urls={
        "Documentation": "https://anl.readthedocs.io/",
        "Changelog": "https://anl.readthedocs.io/en/latest/changelog.html",
        "Issue Tracker": "https://github.com/autoneg/anl/issues",
    },
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.10",
    install_requires=[
        # 'dataclasses; python_version < "3.7"',
        "click",
        "pytest",
        "hypothesis",
        "prettytable",
        "negmas>=0.10.21",
        "tqdm",
        "joblib",
        "jupyter",
        "gif",
        "streamlit",
    ],
    extras_require={},
    setup_requires=["pytest-runner"],
    entry_points={
        "console_scripts": [
            "anl = anl.cli:main",
            "anlv = anl.visualizer.cli:main",
            "anlvis = anl.visualizer.cli:main",
            "anl-vis = anl.visualizer.cli:main",
        ]
    },
)
