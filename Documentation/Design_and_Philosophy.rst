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
* Containerization

Introductory thoughts
~~~~~~~~~~~~~~~~~~~~~

Reproducibility is key in modern scientific discovery. Ideally, *all* software used for science should be maintained, or at least containerized and stored long-term. However, this is rarely the case, especially with personal or smaller team projects: the code developed is generally not documented nor tested and abandoned after the project. With much the same future projects, a similar software then is then being re-invented. This leads to sub-optimal development with code copying from older projects, minimal optimization, and in general lack of re-usability of each software iteration. On the other hand, testing and optimizing code is time-costly, especially when the software is aimed to achieve a highly specific goal (but a slightly different goal each iteration). Similarly, documentation is essentially pointless for a library used *only* by its developer(s), but the lack of it renders the code un-usable in case of a long hiatus in usage/development .

At least this is my **personal experience**, or it may only highlight the lack of my experience in software development...

Since radio astronomy research (more precisely, synthesis imaging & associated pipeline development), uses the same data formats (MS, fits), and a handful of software (e.g. ``CASA``), having a single *personalized* library of the custom code, I use for various projects would solve the problems mentioned above.

Therefore, the idea is, to have a library that I maintain (hopefully) for long-term and so the time spent to optimize the code is not lost. Furthermore, I can re-use (hopefully) all the code I write, especially in terms of pipelines and the associated *unique* data inspection and manipulation routines. Nonetheless, I want to avoid the trap of spending too much time on writing documentation and testing code that I might run only once for a project, and not used by collaborators.

As such, I aim to find a balance in writing *scientific* software and pipelines which falls short to 'commercial' quality intended to use for a wide user-base, but a code which saves time for future me and allows for increasingly faster development and is easy to use for my collaborators (especially the pipelines).

To achieve this, I have the following design goals in mind.

Thoughts on pipelines used in radio astronomy (interferometry)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No one-fit-for all solution exists in large-scale (radio) synthesis imaging and data analysis, despite some community efforts (e.g. ``caracal``). Different instruments and projects, require (and have) different pipelines, despite using the same software under the hood. These pipelines are generally too rigid to have new features or more detailed steps introduced. In addition, workflow management (i.e. distributing jobs to resources) are poorly designed, many cases the pipeline simply being a collection of shell scripts hand-crafted to the given data, with no option for the user to tailor pipelines to the execution environment. This is not a scaleable and flexible solution, and while carefully tuning pipeline parameters by hand is somewhat inevitable, it should be done via *configuration files*. In some pipelines this is possible, but mostly with reduced parameter options exposed to the user and/or too technical so only the black-belt users of the code (who are the developers, in reality) can perform high-level customization of the pipeline.

This environment renders the average user unable to use custom solutions and some simple tasks in a scaleable and automated manner.

To be able to write scaleable and easy-to deploy pipelines, I aim to implement a wrapper around existing code, with (hopefully) options for customizing both the workflow deployment and the parameters of the software used. However, the pipelines included in ``arcane_suite`` are still focused to do a single thing. While, some pipelines can be quite general, ``arcane_suite`` is not a one-fit-for-all solution. It would be hypocritical to say so. It is simply just another pipeline framework, with pre-defined pipelines. I guess, the difference here is that I am the black-belt when new pipelines need to be made with ``arcane_suite``...

Nonetheless, the approach to use a 3rd party workflow manager to deploy various pipelines, which were traditionally deployed by either using a *single* software (with sometimes limited palatalization) or via hand-crafted and so not re-usable pipelines is a **new approach** in this field.

An approach that can help to develop new, quirky pipelines, which, indeed I try to do as science...

Building on existing tools
~~~~~~~~~~~~~~~~~~~~~~~~~~

The aim of ``arcane_suite`` is not to reinvent the wheel, but to use existing software as much as possible. Especially in pipelines that need to scale. The goal is to spend the minimal amount of time on the well-established (but sometimes core) steps in radio astronomy research and rather focus on developing small non-existent *unique* features (and some personal analytic routines). Therefore, most code should aim to provide a comfortable wrapper environment for the various 3rd party software. This approach should enable the relatively easy addition or change of the software used in the pipelines. These wrappers ideally make use of *template* configuration files for the underlying code, with only a few selected parameters -- needed to run the pipeline via ``arcane_suite`` -- are exposed in the ``arcane_suite`` config files. However, the user *should* have more control over the underlying code, by hand-crafting the template files.

Why ``Snakemake``?
~~~~~~~~~~~~~~~~~~

`Snakemake <https://snakemake.github.io/>`_ is a workflow manager designed to deploy simple data-driven pipelines. ``Snakemake`` is scaleable, supports cluster execution and different back-ends (virtual environment, containers). Furthermore, it is robust against failure in highly parallel steps. However, ``Snakemake`` is limited to work with command-line applications, and the parallelism also has to be data-driven.

Radio astronomy is highly data-driven and the data reduction often embarrassingly parallel. Generally the input of a pipeline is some visibility data or image, with each major steps is *modifying existing* or *creating new* data products. Furthermore, the parallel nature of these steps are reflected in the data itself (e.g. parallel processing of each frequency channel). Therefore, majority of data analysis steps can be paralleled and wrapped into ``Snakemake``.

This seems to be a great match.

Using some sort of workflow manager is a *must* to build scaleable pipelines that can run on various environments with the parallel execution and resource management is distributed by the workflow manager. Note that it is unavoidable from the user-end to provide information on the hardware and set the pipeline parameters to match the machine's limitations. However, with ``Snakemake`` this can be done by configuration files, and the user do not need to worry about the execution in detail.

Nonetheless, using ``Snakemake`` is still a somewhat *arbitrary* choice that I made based on previous experience and personal preference...

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

Since ``arcane_suite`` includes executable pipelines, tools and modules (each intended to be used differently), the deployment of these components are quite different.

The core functionality of this library is delivered as a Python *package*. Simply importing the required modules from ``arcane_suite`` makes the code usable in any Python-based code. Based on these core features, I built the __tools__ and __pipelines__.

The pipelines are designed to be deployable, via *initialisation* scripts. For each pipeline, a custom ``*_init_*`` script is created that automaticaly sets up the ``Snakemake`` pipeline based on a config file, and possibly on template files. The idea is, to hide the ``Snakemake`` pipeline from a potential user, and make deployment and development easy for me once the pipeline is created. Such an approach requires no knowledge of ``Snakemake`` from the (potential) users, or extensive interaction with ``Snakemake`` while developing/improving on the pipeline. This is possible since each pipeline is expected to perform a *specific* task. To achieve smooth deployment, the ``Snakefiles`` are shipped with this package and are copied over to a ``working_directory``, in which the pipeline is executed. Therefore, each pipeline is deployed in a user-defined directory, by design.

Tools are (intended to be) simple tasks running as command-line programs. These stand-alone tools are hand-selected to make *some* infrequently re-occuring calculations/tasks available when needed.


Automated data inspection and analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any good pipeline *should* generate not only useful log files, but further analytic plots and files as well. While some of the pipelines use third-party software, which creates automated reports and analytic plots, some additional functionality is desired. As such, a *soft* development aim is to include qualitative and quantitative analytic features in ``arcane_suite``. I intend to implement the most useful features as standalone tools, and if I feel useful, even a *basic* inspection pipeline for different levels of radio astronomy data. The long-term goal is to create *self-contained* reports, similar to, or rather compatible with ``radiopadre``.

Containerization
----------------

To meet the design goals of *reproducibility* and of *flexible deployment*, I intend to provide config files for building containers for the pipelines and for ``arcane_suite`` itself. Ultimately, the goal would be to enable pipeline deployment with *containerized* backed trough the ``*_init_*`` scripts. With such an approach, I or any potential user, can run this software on any hardware via containers, in an 'admin-free' way. This design philosophy is inspired from ``radiopadre``, and so I am also hoping to generate a 'client' library/script that can set up ``arcane_suite`` itself remotely to any machine. However, this is a minor design goal for the future.

Documentation and testing
~~~~~~~~~~~~~~~~~~~~~~~~~

I aim to use `semantic versioning <https://semver.org/>`_ to indicate the backwards compatibility and functionality. I plan to have release notes for major releases.

As mentioned above, the main goal for the documentation is to assist future me with the usage/development of the code in the future. That is, I plan to provide only a high-level documentation formatted to be displayed on `the GitHub page <https://github.com/rstofi/arcane_suite/>`_. While it would be easy to generate a dedicated site for the documentation, I find this approach both sufficient and convenient for me. Consequently, the underlying code is *only* documented in-line. For individual pipelines and tools, I intend to add some kind of ``manual`` that can be read in the command line with more detailed description. However, the documentation of individual *functions* and *objects* are only needed for the developers, who *should* be able to learn the code and find they way around. This is maybe only me, but this is a *personal* code library after all...

Testing is sadly, a heavily neglected part of scientific libraries. In particular, of data-driven code. I plan to ever increase the testing coverage of ``arcane_suite``, I am not a hypocrite. Testing is low on my priority list. Especially, the tricky task of testing code interacting with radio astronomy-specific data, such as MS. While, the code *is* tested during development, I am happy to fix any bug reported. Known issues and bugs are listed in the `backlog <https://github.com/rstofi/arcane_suite/blob/main/Documentation/Backlog.rst>`_ page, together with some *current* development hurdles. I choose this solution to avoid having a conversation with myself on the dedicated `issues <https://github.com/rstofi/arcane_suite/issues>`_ page... but I would prefer if contributors would report issues and start discussions there.

Library structure
-----------------

Some-kind of a minimalist map for the library:

| arcane_suite/
|   ├── Documentation/
|       └── # all the documentation sits here
|   ├──Testing/
|       └── # all testing sits here
|   ├── src/
|       ├── arcane_pipelines/
|           └── # all pipelines live here in a separate directory
|       ├── arcane_utils/
|           └── # all the modules live here, each mdule in a separate file
|       ├── arcane_tools/
|           └── # all tools are here, each in a separate file
|       └── arcane_apps/
|           └── # I plan to put here all the code that creates and manages command-line applications
|   └── Containers
|           └── # I plan to put here configuration files for containers


