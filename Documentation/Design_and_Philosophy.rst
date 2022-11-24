Design and Philosophy
=====================

I am a radio astronomer and not a software engineer/architect. Hence, I mostly learnt to develop code and libraries on my own, within the *academic* framework. As such, most of the code I write is solely for my research purposes, sometimes with the intent to used not only by me, but by collaborators as well. However, I am *not* building 'commersal' tools for the wider community and large collaborations. Therefore, ``arcane_suite`` falls in-between a collection of simple scripts for personal use and commersal software:

``arcane_suite`` is a **public** but **personal software library** for radio astronomy research.

The choices I made during the development process should reflect this nature. That is, the code included and the documentation is mostly collected for (the future) me, but should be useful for my collaborative work and my colleagues if they choose to use this library.

My mindset and the resultant library structure are summarized in:

* `Philosophy`_
* `Library structure`_

Philosophy
----------

This section aims to describe the ideas and philosophy behind ``arcane_suite``. The main ideas for development are the following, most of which are explained in more detail below.

**Major design goals:**

* Build around *existing* commonly used radio astronomy packages
* Reusable and scaleable pre-defined pipelines via ``Snakemake``
* Modular design and internal consistency avoiding redundant functionality
* Scientific-usage focused: easy to deploy and run on cluster environments


**Minor design goals:**

* In-code oriented documentation
* Data-driven testing
* Modularised containerization using smaller, specific containers

Introductory thoughts
~~~~~~~~~~~~~~~~~~~~~

Reproducibility is key in modern scientific discovery. Ideally, *all* software used for science should be maintained, or at least containerized and stored long-term. However, this is rarely the case, especially with personal or smaller team projects: the code developed is generally not documented nor tested and abandoned after the project. With much the same future projects, a similar software then is the being re-invented. This leads to sub-optimal development with code copying from older projects, minimal optimization, and in general lack of re-usability of each software iteration. On the other hand, testing and optimizing code is time-costly, especially when the software is aimed to achieve a highly specific goal (but a slightly different goal each iteration). Similarly, documentation is essentially pointless for a library used *only* by its developer(s), but the lack of it renders the code un-usable in case of a long hiatus in usage/development .

At least this is my **personal experience**, or it may only highlight the lack of my experience in software development...

Since radio astronomy research (more precisely, synthesis imaging & associated pipeline development), uses the same data formats (MS, fits), and a handful of software (e.g. CASA), having a single *personalized* library of the custom code, I use for various projects would solve the problems mentioned above.

Therefore, the idea is, to have a library that I maintain (hopefully) for long-term and so the time spent to optimize the code is not lost. Furthermore, I can re-use (hopefully) all the code I write, especially in terms of pipelines and the associated *unique* data inspection and manipulation routines. Nonetheless, I want to avoid the trap of spending too much time on writing documentation and testing code that I might run only once for a project, and not used by collaborators.

As such, I aim to find a balance in writing *scientific* software and pipelines which falls short to 'commercial' quality intended to use for a wide user-base, but a code which saves time for future me and allows for increasingly faster development and is easy to use for my collaborators (especially the pipelines).

To achieve this, I have the following design goals in mind.

Thoughts on pipelines used in radio astronomy (interferometry)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No one-fit-for all solution exists in large-scale (radio) synthesis imaging and data analysis. Different instruments and projects, require (and have) different pipelines, despite using the same software under the hood. These pipelines are generally too rigid to have new features or more detailed steps introduced. In addition, workflow management (i.e. distributing jobs to resources) are poorly designed, many cases the pipeline simply being a collection of shell scripts hand-crafted to the given data, with no option for the user to tailor pipelines to the execution environment. This is not a scaleable and flexible solution, and while carefully tuning pipeline parameters by hand is somewhat inevitable, it should be done via *configuration files*. In some pipelines this is possible, but mostly with reduced parameter options and/or too technical so only the black-belt users of the code (who are the developers, really) can perform high-level customization.

This environment renders the average user unable to use custom solutions and some simple tasks in a scaleable and automated manner.

To be able to write scaleable and easy-to deploy pipelines, I aim to implement a wrapper around existing code, with (hopefully) options for customizing both the workflow deployment and the parameters of the software used. However, the pipelines included in ``arcane_suite`` are still focused to do a single thing. While, some pipelines can be quite general, ``arcane_suite`` is not a one-fit-for-all solution. It would be hypocritical to say so. It is simply just another pipeline framework, with pre-defined pipelines. I guess, the difference here is that I am the black-belt when new pipelines need to be made with ``arcane_suite``....

Nonetheless, the approach to use a 3rd party workflow manager to deploy various pipelines, which were traditionally deployed by either using a *single* software (with sometimes limited parallelization) or via hand-crafted and so not re-usable pipelines is a **new approach** in this field.

An approach that can help to develop new, quirky pipelines, which, indeed I try to do as science...

Building on existing tools
~~~~~~~~~~~~~~~~~~~~~~~~~~

The aim of ``arcane_suite`` is not to reinvent the wheel, but to use existing software as much as possible. Especially in pipelines that need to scale. The goal is to spend the minimal amount of time on the well-established (but sometimes core) steps in radio astronomy research and rather focus on developing small non-existent *unique* features (and some personal analytic routines). Therefore, most code should aim to provide a comfortable wrapper environment for the various 3rd party software. This approach should enable the relatively easy addition or change of the software used in the pipelines.

Why ``Snakemake``?
~~~~~~~~~~~~~~~~~~

`Snakemake <https://snakemake.github.io/>`_ is a workflow manager designed to deploy simple data-driven pipelines. ``Snakemake`` is scaleable, supports cluster execution and different back-ends (virtual environment, containers). Furthermore, it is robust against failure in highly parallel steps. However, ``Snakemake`` is limited to work with command-line applications, and the parallelism also have to be data-driven.

Radio astronomy is highly data-driven and the data reduction often embarrassingly parallel. Generally the input of a pipeline is some visibility data or image, with each major steps is *modifying existing* or *creating new* data products. Furthermore, the parallel nature of these steps are reflected in the data itself (e.g. parallel processing of each frequency channel). Therefore, majority of data analysis steps can be paralleled and wrapped into ``Snakemake``.

This seems to be a great match.

Using some sort of workflow manager is a *must* to build scaleable pipelines that can run on various environments with the parallel execution and resource management is distributed by the workflow manager. Note that it is unavoidable from the user-end to provide information on the hardware and set the pipeline parameters to match the machine's limitations. However, with ``Snakemake`` this can be done by configuration files, and the user do not need to worry about the execution in detail.

Modularity and internal consistency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``arcane_suite`` consists of pipelines, tools and modules. Whilst these components are meant to used separately, the underlying code should be highly interconnected.

With (hopefully) a wide-variety of pipelines, ``arcane_suite`` is expected to perform extremely different tasks. These tasks, however, can be using similar data products (i.e. MS) or operating on similar parameter space (i.e. visibility space). Therefore, different components should be able to call the same core routines.

To accommodate the various pipelines, ``arcane_suite`` aims to be highly modular, with the modules organized around:

* data structure
* software
* parameter space

Ergo, if a pipeline needs to interact with a Measurement Set (MS), it either calls the module handling MS' or a module providing a wrapper for a software using MS' input, but not mixing different types of MS' reading.

As such, each distinct functionality should be implemented only *once*. The interaction between the models solved via using ``Python`` objects such as ``numpy.ndarray``. This requires a high level of internal consistency. As such, the goal is to have routines operating with highly specific inputs or highly general inputs. For example, a code operation on time-series data should have the data input in a general array of float format, rather than some time-specific format, while code working with MS should read in MS only. Similarly, the output of functions should be either highly specific or general. For example, a routine fetching time-series data from an MS, should return an array of float. The data re-formatting should handled within individual modules. Such approach slows down execution due to the conversion overhead introduced. Nonetheless, internal consistency is key to minimize redundancy and conflict between modules and pipelines.

Deployment
~~~~~~~~~~


Automated data inspection and analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



Documentation and testing
~~~~~~~~~~~~~~~~~~~~~~~~~


Library structure
-----------------
