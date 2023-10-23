#!/bin/bash -l

#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --job-name='pre_OTF_flagging'
#SBATCH --cpus-per-task=30
#SBATCH --mem=120GB
#SBATCH --output=runjob_%j_stdout.log
#SBATCH --error=runjob_%j_stderr.log
#SBATCH --time=04:00:00

CONTAINER='/project/ls-mohr/MeerKAT/singularity_containers/caracal_container.sif'

module load singularity/v3.8.1 #We absolutely need this as ther is a problem with apptainer

echo $SINGULARITY_TMPDIR
mkdir -p  $SINGULARITY_TMPDIR

singularity exec --bind /project/ls-mohr/MeerKAT:/MeerKAT ${CONTAINER} caracal -c flagging.yml -ct singularity -sid /MeerKAT/singularity_containers/stimela_images_for_caracal/

