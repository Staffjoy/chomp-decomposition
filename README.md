![Logo](https://i.imgur.com/deZ3wCa.jpg)

# Chomp - Service for computing shifts from forecasts

[![Build Status](https://travis-ci.org/Staffjoy/chomp-decomposition.svg?branch=master)](https://travis-ci.org/Staffjoy/chomp-decomposition) [![Moonlight contractors](https://www.moonlightwork.com/shields/python.svg)](https://www.moonlightwork.com/for/python?referredByUserID=1&referralProgram=maintainer&referrerName=Staffjoy) [![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg)](https://hub.docker.com/r/staffjoy/chomp-decomposition/) [![PyPI version](https://badge.fury.io/py/chomp.svg)](https://badge.fury.io/py/chomp)

[Staffjoy is shutting down](https://blog.staffjoy.com/staffjoy-is-shutting-down-39f7b5d66ef6#.ldsdqb1kp), so we are open-sourcing our code. Chomp is an applied mathematics microservice for decomposing hourly demand into shifts of variable length. This repo was intended to be a proof of concept. It worked so well in production that we never rewrote it. My intention was to rewrite it into a more parallel language, such as Go, in order to take advantage of multiple cores. It served production traffic from June 2016 to March 2017 with zero modification or production errors.

## Self-Hosting

If you are self-hosting Chomp, please make sure that you are using version `>=0.24` of the `staffoy` client (in `requirements.txt`). Then, modify `chomp/tasking.py` to include your custom domain - when initializing `Client()`, pass in your custom URL base, e.g. `Client(url_base="https://staffjoy.example.com/api/v2/, key=config.STAFFJOY_API_KEY, env=config.ENV)`,

## Algorithm

![Chomp converts forecasts to shifts](https://i.imgur.com/i8enKgO.png)

Chomp solves a type of packing problem similar to a [bin packing problem](https://en.wikipedia.org/wiki/Bin_packing_problem). It tries to tessellate when shifts start and how long they last in order to best match staffing levels to forecasts. It does this subject to the minimum and maximum shift length.

Chomp uses techniques from [branch and bound algorithms](https://en.wikipedia.org/wiki/Branch_and_bound), and adds in subproblem generation, preprocessing techniques, feasibility detection, heuristics, and caching. [Learn more in the Chomp launch blog post.](https://blog.staffjoy.com/introducing-chomp-computing-shifts-from-forecasts-21315f46aadc#.xa306ltre)


## Credit

This repository was conceived and authored in its entirety by [@philipithomas](https://github.com/philipithomas). This is a fork of the internal repository. For security purposes, the Git history has been squashed and client names have been scrubbed from tests. (Whenever there was a production issue, we added a functional test to the repo.)

## Usage

You can install Chomp locally with `pip install --upgrade chomp`. Or, use the [docker image](https://hub.docker.com/r/staffjoy/chomp-decomposition/) to interface Chomp with [Staffjoy Suite](https://github.com/staffjoy/suite). 


Chomp was designed to handle one week of scheduling at an hourly granularity. However, the package is unitless and hypothetically support weeks of any length of time at any granularity.

```
from chomp import Decompose

demand = [0, 0, 0, 0, 0, 0, 0, 5, 5, 7, 8, 6, 6, 7, 7, 7, 9, 9, 6, 5,
            4, 4, 0, 0]
min_length = 4
max_length = 8
d = Decompose(demand, min_length, max_length)
d.calculate() # Long step - runs calculation
d.validate() # Mainly for testing, but quick compared to calculate step. Verifies that solution meets demand. 
d.get_shifts() # Returns a list of shifts, each of which have a start time and length
# [{'start': 7, 'length': 4}, {'start': 7, 'length': 4}, {'start': 7, 'length': 4}, {'start': 7, 'length': 4}, {'start': 7, 'length': 4}, {'start': 9, 'length': 4}, {'start': 9, 'length': 4}, {'start': 10, 'length': 4}, {'start': 11, 'length': 4}, {'start': 11, 'length': 4}, {'start': 11, 'length': 4}, {'start': 13, 'length': 4}, {'start': 13, 'length': 5}, {'start': 13, 'length': 5}, {'start': 14, 'length': 4}, {'start': 15, 'length': 4}, {'start': 15, 'length': 5}, {'start': 15, 'length': 7}, {'start': 16, 'length': 6}, {'start': 16, 'length': 6}, {'start': 17, 'length': 5}]
```

Chomp seeks to minimize the time worked, i.e. `sum([shift.length for shift in shifts])`, where `min_length <= shift.length <= max_length` for every shift.
## Environment Variables

This table intends to explain the main requirements specified in `app/config.py`. This configuration file can be manually edited, but be careful to not commit secret information into the git repository. Please explore the config file for full customization info.

Name | Description | Example Format
---- | ----------- | --------------
ENV | "prod", "stage", or "dev" to specify the configuration to use. When running the code, use "prod". | prod
STAFFJOY_API_KEY | Api key for accessing the Staffjoy API that has at least `sudo` permission level | 
SYSLOG_SERVER | host and port for a syslog server, e.g. [papertrailapp.com](http://papertrailapp.com) | logs2.papertrailapp.com:12345

## Running

Provision the machine with vagrant. When you first run the program or when you change `requirements.txt`, run `make requirements` to install and freeze the required libraries. 

```
vagrant up
vagrant ssh
# (In VM)
cd /vagrant/
make dependencies
```

## Caching

Subproblems are cached based on their demand, minimum shift length, and maximum shift length. This prevents re-calculation of problems whose answer we know. Currently this cache lives on the box in Memcache. Clearly, this means that a deploy, restart, etc can trigger a loss of all historical data. For now, this is by design so that theroetical efficiency gains by newer builds can be realized. In the future, we may want to tag things that are at perfect optimality and preserve them by using a dedicated memcache cluster. Realistically though, most repeated problems will be within the same "week" by orgs that repeat demand for all weekdays or the like. 

## Formatting

This library uses the [Google YAPF](https://github.com/google/yapf) library to enforce PEP-8. Using it is easy - run `make fmt` to format your code inline correctly. Failure to do this will result in your build failing. You have been warned.

To disable YAPf around code that you do not want changed, wrap it like this:

```
# yapf: disable
FOO = {
    # ... some very large, complex data literal.
}

BAR = [
    # ... another large data literal.
]
# yapf: enable
```
