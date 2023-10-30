# syntax=docker/dockerfile:1

#Original dockerfile by Nicola Malavasi 

#Builder image: lighter to download, we use it ot install some stuff- python image
FROM python:3.8.16-slim-bullseye as builder

#Update apt-get and install useful packages: python-is-python3 to symlink python command to python3 command, git, wget, xz-utils, pip3
RUN apt-get update && apt-get -y install wget xz-utils git time

#Download CASA tarball
RUN wget https://casa.nrao.edu/download/distro/casa/release/rhel/casa-6.5.2-26-py3.8.tar.xz

#Extract in home directory
RUN tar -xvf casa-6.5.2-26-py3.8.tar.xz

#Make directory for python packages
RUN mkdir requirements_folder

#Git clone arcane suite
RUN git clone https://github.com/rstofi/arcane_suite.git

#Change folder to the arcane_suite
WORKDIR /arcane_suite

#Set specific commit
RUN git checkout d7d394fc03375b3efa7cc2711834462c812473ad

#Install all requirements
RUN pip3 install --target=/requirements_folder -r ./requirements.txt



#Use kernsuite image as it contains python-casacore and chgcentre
FROM kernsuite/base:7 as runner

#Install python-casacore and chgcentre
RUN docker-apt-install python3-casacore chgcentre

#Copy what previously installed
COPY --from=builder /requirements_folder /usr/local/src/
COPY --from=builder /requirements_folder/bin /usr/bin/
COPY --from=builder /casa-6.5.2-26-py3.8 /usr/local/src/casa_from_container/
COPY --from=builder /arcane_suite /usr/local/src/arcane_suite/

#Update apt-get and install useful packages: python-is-python3 to symlink python command to python3 command pip3
RUN apt-get update && apt-get -y install python-is-python3 graphviz python3-pydot python3-pip

#Update PYTHONPATH
ENV PYTHONPATH=$PYTHONPATH:/usr/local/src

#Create symbolic link to point to the correct python
RUN ln -s /usr/bin/python3.8 /usr/local/bin/python

#Create symbolic link for casa
RUN ln -s /usr/local/src/casa_from_container/bin/casa /usr/local/bin/casa

#Change folder to the arcane_suite
WORKDIR /usr/local/src/arcane_suite

#Install the arcane arcane_suite
RUN pip3 install -e ./
