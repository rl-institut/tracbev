# Quickstart guide to TracBEV

## What is TracBEV?

TracBEV is a **t**ool for the **r**egional **a**llocation of **c**harging infrastructure. In practice this allows users to use results generated via [SimBEV](https://github.com/rl-institut/simbev) and place the corresponding charging points on a map. These are split into the 4 use cases hpc, public, home and work.

## Installation

- clone repository to your local machine
- install requirements found in requirements.txt (virtualenv recommended)
- setup.py is not working yet

## Get Data

The required data to run this tool will soon be available here.
For now it can be requested from us directly.

## Running TracBEV

After adding the data directory in your local clone, simply run `main.py`.

As default, this run uses the `tracbev_config.cfg` in the `scenarios` directory. `main.py` takes a file name as an optional parameter, which allows the use of new config files. 
