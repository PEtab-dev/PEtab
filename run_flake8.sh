#!/bin/sh

python3 -m flake8 --exclude=build,doc,example,tmp --extend-ignore=F405,F403
