Backlog
=======

This page is a simple backlog, I try to keep up to date. I am not following any strict development plan, simply collect various tasks here.

Ongoing stories
---------------

Parts of the (sometimes unfinished) code, I am currently working.

    - finish the function(s):
    - finish the app(s):
    - write documentation for: 
    - check bugs for: ``otfms_pointing_diagnostics``
    - add to Snakemake workflow:

    - add functionality of:
        - using names not ID's to ``create_field_ID_RA_Dec_plot`` + propagate it into the pipeline
        - split the calibrators
        - plot the calibrator pointing in the pipeline

Known bugs/issues
-----------------

Bugs and issues, I am aware and should fix, but are not currently affecting the code performance.

    - he  ``split_calibrators`` rule in the ``otfms`` pipeline does not work
    - similarly, fix the ``merge_otf_pointings_and_calibrators`` rule in ``otfms``
    - there leftover ``CASA`` log ad param files in the ``otfms`` pipeline
    - handeling empty calibrator fields list in ``otfms``

Goals for version update
------------------------

My goals for a minor version update.

    - add rules for generating analytic plots (before and after phase rotation) in ``otfms``
    - fix the bugs with the calibrator skip and merge in ``otfms``
    - add a rule to clean up the intermediate files in ``otfms``
    - finish the `design & philosophy <https://github.com/rstofi/arcane_suite/blob/main/Documentation/Design_and_Philosophy.rst>`_ page
    - add documentation for the ``otfms`` pipeline
    - factorize the tasks(i.e. from the code add to casa_wrapper): ``run_:casa_executable``, ``create_casa_merge_executable`` + same for split and add listobs a s an option to both


Long-term goals
---------------

Some of my ideas for the future directions of the code.

    - add ``arcane_suite`` to pip
    - add testing module based on ``ChatGPT`` code
    - make a separate ``arrcane_tools`` library

