Quickstart guide to TracBEV
===========================

What is TracBEV?
----------------

TracBEV is a tool for the regional allocation of charging infrastructure. In practice this allows users to use results generated via `SimBEV <https://github.com/rl-institut/simbev>`_ and place the corresponding charging points on a map. These are split into the 4 use cases hpc, public, home and work.

Installation
------------

- clone repository to your local machine
- install requirements found in requirements.txt (virtualenv recommended)
- setup.py is not working yet

Get Data
--------

The required data to run this tool can be downloaded `here <https://zenodo.org/record/6466480#.YmE9xtPP1hE>`_.

Running TracBEV
---------------

After adding the data directory in your local clone, simply run `main.py`.

As default, this run uses the `tracbev_config.cfg` in the `scenarios` directory. `main.py` takes a file name as an optional parameter, which allows the use of new config files. 

License
-------

TracBEV is licensed under the MIT License as described in the file `LICENSE <https://github.com/rl-institut/tracbev/blob/dev/LICENSE>`_.
