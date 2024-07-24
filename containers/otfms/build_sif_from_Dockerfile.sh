#!/bin/bash/

sudo docker build -t local/otf_rotation_fix:latest .
sudo singularity build otf_rotation_fix.sif docker-daemon://local/otf_rotation_fix:latest
