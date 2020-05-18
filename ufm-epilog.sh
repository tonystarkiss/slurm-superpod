#!/bin/bash
echo "==Post job==:"
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd $SCRIPTPATH
python ufm_slurm_epilog.py -i $SLURM_JOBID

