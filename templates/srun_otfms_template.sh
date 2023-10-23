#!/bin/bash
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=30 #Out of 64 available
#SBATCH --mem=224G #Out of 512GB
#SBATCH --time=4:00:00 #46h for a full 1.5h tracking MS
#SBATCH --error=runjob_%J_stderr.log
#SBATCH --output=runjob_%J_stdout.log

CONTAINER='/project/ls-mohr/MeerKAT/singularity_containers/otfms.sif'

#module load singularity/v3.8.1

apptainer exec --bind /project/ls-mohr/MeerKAT:/MeerKAT ${CONTAINER} sh -c {path_to_pipeline}/otfms_worker.sh >> $(pwd)/worker.log #$(pwd) yields the wrong path, i.e. not the mounted path

