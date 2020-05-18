#!/bin/bash
echo "==Pre job==:"
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
cd $SCRIPTPATH
python ufm_slurm_prolog.py -i $SLURM_JOBID || true