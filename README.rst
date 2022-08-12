Quickstart guide to TracBEV
===========================

What is TracBEV?
----------------

TracBEV is a tool for the regional allocation of charging infrastructure. In practice this allows users to use results generated via `SimBEV <https://github.com/rl-institut/simbev>`_ and place the corresponding charging points on a map. These are split into the 4 use cases hpc, public, home and work.

Installation
------------

- clone repository to your local machine

Linux:
- install requirements found in requirements.txt (virtualenv recommended) with pip

Windows:
- install using conda by opening Anaconda Prompt, navigating into the tracbev directory and using the command
``conda env create -f environment.yml``
- if install fails on Windows, check out `this link <https://stackoverflow.com/questions/50876702/cant-install-fiona-on-windows>`_

Get Data
--------

The required data to run this tool can be downloaded `here <https://zenodo.org/record/6466480#.YmE9xtPP1hE>`_.

Running TracBEV
---------------

After adding the data directory in your local clone, simply run the module ``tracbev``:

``python -m tracbev``

As default, this run uses the ``default_scenario`` in the ``scenarios`` directory.
The module takes a scenario as an optional parameter, which allows the use of new config files.

If you dont have any SimBEV data or just want all potential points in the region, use the argument ``--mode potential`` when starting TracBEV.

License
-------

TracBEV is licensed under the MIT License as described in the file `LICENSE <https://github.com/rl-institut/tracbev/blob/dev/LICENSE>`_.
