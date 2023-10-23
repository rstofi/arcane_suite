#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --job-name='test_pipeline_1630519596'
#SBATCH --cpus-per-task=8
#SBATCH --mem=40GB
#SBATCH --output=runjob_%j_stdout.log
#SBATCH --error=runjob_%j_stderr.log
#SBATCH --time=1:00:00 #All these params are set to enable cleaning directories in the beginning...

CONTAINER='/project/ls-mohr/MeerKAT/singularity_containers/caracal_OTF_container.sif'

module load singularity/v3.8.1 #We absolutely need this as ther is a problem with apptainer

echo $SINGULARITY_TMPDIR
mkdir -p  $SINGULARITY_TMPDIR

echo $(pwd)

singularity exec --bind /project/ls-mohr/MeerKAT:/MeerKAT ${CONTAINER} python master_for_OTF_imaging_and_selfcal_workers.py -c imaging_and_selfcal_pipeline.cfg
