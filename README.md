![Logo](https://i.imgur.com/deZ3wCa.jpg)

# Chomp - Service for computing shifts from forecasts

[![Build Status](https://travis-ci.org/Staffjoy/chomp-decomposition.svg?branch=master)](https://travis-ci.org/Staffjoy/chomp-decomposition) [![Moonlight](https://img.shields.io/badge/contractors-1-brightgreen.svg)](https://moonlightwork.com/staffjoy) [![Docker Automated build](https://img.shields.io/docker/automated/jrottenberg/ffmpeg.svg)](https://hub.docker.com/r/staffjoy/chomp-decomposition/)

[Staffjoy is shutting down](https://blog.staffjoy.com/staffjoy-is-shutting-down-39f7b5d66ef6#.ldsdqb1kp), so we are open-sourcing our code. Chomp is an applied mathematics microservice for decomposing hourly demand into shifts of variable length. It uses techniques from [branch and bound algorithms](https://en.wikipedia.org/wiki/Branch_and_bound), and adds in subproblem generation, preprocessing techniques, feasibility detection, heuristics, and caching. 

This repo was intended to be a proof of concept. It worked so well in production that we never rewrote it. My intention was to rewrite it into a more parallel language, such as Go, in order to take advantage of multiple cores. It served production traffic from June 2016 to March 2017 with zero modification or production errors.

## Credit

This repository was conceived and authored in its entirety by [@philipithomas](https://github.com/philipithomas). This is a fork of the internal repository. For security purposes, the Git history has been squashed and client names have been scrubbed from tests. (Whenever there was a production issue, we added a functional test to the repo.)

### Environment Variables

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
