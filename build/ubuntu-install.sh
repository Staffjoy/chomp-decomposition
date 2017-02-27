#!/bin/bash
set -e

sudo apt-get update --yes --force-yes

# Sometimes ubuntu needs these software-properties repos :-(
sudo apt-get install --yes --force-yes build-essential libffi-dev libssl-dev cmake expect-dev \
    python python-dev curl python-setuptools python-software-properties

# For now, we are putting memcache in dev, stage, and prod
# (including inside the docker container)
sudo apt-get install --yes memcached

sudo easy_install -U pip

sudo apt-get update --yes --force-yes # Re-update

# Set env variable that we are in dev
echo "echo 'export env=\"dev\"' >> /etc/profile" | sudo bash
