Backlog
=======

This page is a simple backlog, I try to keep up to date. I am not following any strict development plan, simply collect various tasks here.

Ongoing stories
---------------

Parts of the (sometimes unfinished) code, I am currently working.

    - finish the function(s):
    - finish the app(s): ``arcane_init_isaac``
    - write documentation for: both pipelines
    - check bugs for:
    - add to Snakemake workflow:
        - [``otfms``] to have the times, and RA, Dec coordinates added to the OTF field names file
        - [``isaac``] everything

    - add functionality of:
        - make a separate file for (unit ?) conversions
       
Known bugs/issues
-----------------

Bugs and issues, I am aware and should fix, but are not currently affecting the code performance.

    - handeling empty calibrator fields list in ``otfms``
    - sub-optimal calls to run ``CASA`` tasks in the ``otfms`` pipeline
    
Goals for version update
------------------------

My goals for a minor version update.

    - add documentation for the ``otfms`` and ``isaac`` pipelines
    - factorize the tasks(i.e. from the code add to casa_wrapper): ``run_:casa_executable``, ``create_casa_merge_executable`` + same for split and add listobs as an option to both


Long-term goals
---------------

Some of my ideas for the future directions of the code.

    - add ``arcane_suite`` to pip
    - add testing module (maybe based on ``ChatGPT`` code ?)
    - create the ``arrcane_tools`` library
    - move all current command-line scripts under a 'master' command line script e.g. ``arcane_pipeline_wizard`` with the task (and it's arguments) as the input arguments
    - similarly, create an ``arcane_toolbox`` 'master' command-line tool for the tools
    - add container config files

