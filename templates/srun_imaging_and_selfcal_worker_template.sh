#!/bin/bash -l
  
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --job-name='job'
#SBATCH --cpus-per-task=30
#SBATCH --mem=75GB #56
#SBATCH --output=runjob_%j_stdout.log
#SBATCH --error=runjob_%j_stderr.log
#SBATCH --time=4:00:00 #32 for imaging run

worker=''
cfg=''
output_dir=''
run_dir=''
target=''

#Caracal should be available
CONTAINER='/project/ls-mohr/MeerKAT/singularity_containers/caracal_OTF_container.sif'

module load singularity/v3.8.1 #We absolutely need this as ther is a problem with apptainer

echo $SINGULARITY_TMPDIR
mkdir -p  $SINGULARITY_TMPDIR

echo $(pwd)

singularity exec --bind /project/ls-mohr/MeerKAT:/MeerKAT ${CONTAINER} python ${worker} -c ${cfg} -o ${output_dir} -r ${run_dir} -t ${target}
