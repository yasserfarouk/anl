# ANL Documentation

This repository is the official platform for running ANAC Automated Negotiation Leagues (starting 2024). It will contain a package
called `anlXXXX` for the competition run in year XXXX. For example anl2024 will contain all files related to the
2024's version of the competition.

This package is a thin-wrapper around the [NegMAS](https://negmas.readthedocs.io) library for automated negotiation. Its main goal is to provide the following functionalities:

1. A set of utility functions to run tournaments in the same settings as in the ANL competition. These functions are always called `anl20XX_tournament` for year `20XX`.
1. A CLI for running tournaments called `anl`.
1. A place to hold the official implementation of every strategy submitted to the ANL competition after each year. These can be found in the module `anl.anl20XX.negotiators` for year `20XX`.

The official website for the ANL competition is:
[https://scml.cs.brown.edu/anl](https://scml.cs.brown.edu/anl)


## Installation

    pip install anl

You can also install the in-development version with::

    pip install https://github.com/autoneg/anl/archive/master.zip


## Documentation

* Documentation for the ANL package: [https://yasserfarouk.github.io/anl/](https://yasserfarouk.github.io/anl/)
* Documentation for the NegMAS library: [https://negmas.readthedocs.io](https://negmas.readthedocs.io)


## CLI

After installation, you can try running a tournament using the CLI as:

```bash
anl tournament2024
```

To find all the parameters you can customize for running tournaments run:

```bash
anl tournament2024 --help
```


