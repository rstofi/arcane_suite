## Creating apptainer image from Dockerfile

Use the following commands (needs `sudo` privilige):

```bash
sudo docker build -t local/otf_rotation_fix:latest .
sudo singularity build otf_rotation_fix.sif docker-daemon://local/otf_rotation_fix:latest
```
