#!/bin/bash

#Simple script to reformat *all* .py scripts to pep8 format guides using the autopep8 package

find -type f -wholename './*.py' -exec autopep8 --in-place --verbose -a -a -a -a -a -r --max-line-length 79 '{}' --ignore-local-config \;
