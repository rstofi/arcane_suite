#!/bin/bash

arcane_init_otfms -c {path_to_pipeline}/otfms_pipeline.cfg
cd {path_to_pipeline} 
snakemake --cores 30

