Arbitrary Radio astronomiCAl pipeliNE suite (arcane_suite)
==========================================================

Introduction
------------

`arcane_suite` is a collection of *arbitrary* analitycs and utility tools & libararies and pre-defined `Snakemake <https://snakemake.github.io/>`_ pieplines, that I use for some of my projects. As such, the aim of this library is to have most of my own code in the same place, and to avoid copy and paste code for various projects. Furthermoe, I wanted to develop a framework, in which I can build easy-to-use piepelines using `Snakemake`, since many radio astronomical pipelines are data-driven, yet emberassingly parallel and simple at the same time.

Installation
------------

You can install the latest releas from source only at the moment.

Usage and contribution
----------------------

`arcane_suite` is primarily developed for personal use, except for *some* pipelines, which are developed for collaborations. Nonetheless, the code is open-source and open-acces for anyone to use, including the various libraries pipeline and tools.

Contribution of any form is more than welcome and I aim to fix any bugs as quckly as possible.


Documentation and testing
-------------------------

Documentation is mostly embedded in the code itself, pluss an additional a brief description of the libraries and pipelines included under the `Documentation <https://github.com/rstofi/arcane_suite/blob/master/Documentation/README.rst>`_ folder. The Documentation is designed to be readable in GitHub, and there is no plan to set up a more serious online documentation yet.

Testing of the code is sparse, since some components are data-driven and some are tested on large data sets. However, I try to add testing with time.

These design choices are driven by the fact, that the code is primarily developed for my own usage and not for wider distribution.

Copyright and licence
---------------------

`arcane-suite` is created by Kristof Rozgonyi and can be distributed/used under the terms of the GNU General Public License V3.

@2022 Kristof Rozgonyi
