# OTF imaging cookbook for RBG
----

A quick and dirty guide to reduce OTF data on RBG.

----
## Data preparation
----

All raw data should live under `/project/ls-mohr/MeerKAT/raw/{obs_ID}`

**Never** touch the real data as it meant to be ***read only***!

If you ever need to modify this data, create a separate MS somewhere via `CASA`.

Some notes though:

- use `CASA` trough `singularity` backend on an interactive `slurm` job
- know your data! (i.e. use `listobs` and similar tools)

## Input data
----

The input data is organized in *epochs*. Each epoch directory contains the following input data:

- **OTF_{obs_ID}.ms**: the MS containing the *raw* (i.e. non-OTF-corrected) visibility data and calibrators. For L-band data we only have primary calibrators opbserved.
- **{obs_ID}_reference_antenna_pointing.npz**: a binary file containing the *reference antenna* RA and Dec coordinates as a function of time. This file is needed to perform the OTF-correction step.
- **{obs_ID}_noise_diode.json**: a simple json file containing the noise-diode period and start time. This is used to flag the noise-diodes (during the OTF-correction step).

----
## Data access and the `singularity` backend
----

The singularity containers currently live under `/project/ls-mohr/MeerKAT/singularity_containers/`

Basically the partition `/project/ls-mohr/` is not visible from a singularity container (even if you run it from there), and so when running code with `singularity` backend, one needs to mount the correct path to the data.

Fore example use `--bind /project/ls-mohr/MeerKAT:/MeerKAT ${CONTAINER}` switch in the `singularity` command, where `${CONTAINER}` points to the .sif file used. With such a setup anythin under `/project/ls-mohr/MeerKAT/` can be I/O accessible as `/MeerKAT/`.

**Important**: the path visible from the containers needs to be provided to any software running within the container, and so in the configuration files as well!

Note that I use the conversion above in all my scripts and examples, hope it is not hard-coded anywhere...

### `singularity` vs `apptainer` and `caracal`:
----
While I use the term `singularity` trough this cookbook, and in my example codes, it is depreciated and replaced by `apptainer`. Since, our current `caracal` setup does not follow this, it is sometimes mandatory to use `singularity`. However, for some codes `apptainer` can be used as well.

When using `caracal` via `slurm` we need to load in the `singularity` module and create some folders for `caracal` to be able to run as it is not compatible with `apptainer`.

An example setup:

```shell
module load singularity/v3.8.1 #We absolutely need this as ther is a problem with apptainer

echo $SINGULARITY_TMPDIR
mkdir -p  $SINGULARITY_TMPDIR
```

There is some [ongoing work](https://github.com/caracal-pipeline/caracal/issues/1508) to make `apptainer work` but I haven't got around it yet...

----
## Directory structure, run- and results- directories
----

For the demo, and for future processing, I am thinking about setting up the following directory tree:

```
/{pipeline_version_X}
├── code
│   ├── {some_script_needed}
│   └── ...
├── {pipeline_RUN_version_X}
│   └── {obs_ID_0}
│   │   ├── crosscal
│   │   ├── flagging
│   │   ├── OTF_correction
│   │   └── imaging_and_selfcal
│   │
│   └── {obs_ID_N}
│       └── ...
│
└── templates
    ├── {some_template_file_needed}
    └── ...

```

Ideally the `singularity` containers should go in the top level tho have everything self-contained for each *version* of the pipeline. Of course, if the pipeline is expected not to change, the folders `code` and `templates` could go somewhere central. Regardless, every pipeline run (e.g. with different imaging crosscal parameters) should have it's own separate top-level directory. The data is organized in a per-epoch basis, with each epoch having the same file structure. Each sub-directory per epoch corresponds to a pipeline step.

At the moment each step can be executed via a `slurm` job (except the imaging and selfcal step, but see that later). These steps should be executed from within the corresponding sub-directory to be self-contained (i.e. execution-, config- and log-files and the results are in the same directory).

### the *MS* and *output* directories
----

For the `caracal`-based tasks the `msdir` and `output` directories could be the same, but I **consistently** specify them as `{path_to_task_folder}/MS` and `{path_to_task_folder}/output`. This notation can be changed of course, but unfortunately, I have this directory structure ***hard-coded*** in some of my scripts with only the top-level directory (i.e. `{path_to_task_folder}/`) needed as an argument for some functions/apps. That is, if this structure is not followed, my code will not find the required paths to operate...

----
## OTF-format MS creation: first pipeline steps
----

At the moment, each of these steps need to be set up and run manually, but I plan to have a script that can set up and run all these steps (in a linear fashion due to low run times), based on the data ID and template files. Ideally each of these steps needs to be run only once. Furthermore all these steps only take a few hours to run. As such, the simple script provided, should be sufficient to get the job done in a good-enough fashion wit no real need of further optimization.

Note that the reference antenna used in the templates, and trough my data processing is **m008*. However, in some observations this antenna was not used, in which cases ***use antenna m009***! The reasoning behind this is to have consistency between the reference antenna positions used for the OTF correction and the reference antenna used for calibration.

### crosscal
----

The first step of the pipeline (can be paralleled with the flagging step). This step of the pipeline requires **manual checking!** Ideally one wants to check the calibration solutions before proceeding. In a "perfect" world fully-automated calibration exist, but at the moment we need to make sure, that the data quality is *good enough* and if not, we need to tune the calibration process.

Note that this pipeline is a ***simple `caracal` call***. Ergo, we are limited to what is possible via `caracal`, for the cost of this step being easy to understand (plus I had to do no coding for this).

Note that for the L-band data we observed non secondary calibrator sources. Therefore, I use the primary calibrator as the secondary calibrator. This means additional iteration on some gain terms (K,B,G) and that I use the primary calibrator to derive the flux scale (solve for F).

### flagging
----




### OTF correction
----


### imaging and selfcal
----

NOTE: broken symlinks on RBG + the symlinking option could be broken if the run and caltbales dirs are mounted veirdly... this should not be a problem on other systems and could be disabled



### prefixes and naming convention
----



### templates used
----












































