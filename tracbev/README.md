# verortung_simbev

## Download/install
- clone repository to your local machine
- install requirements found in requirements.txt (virtualenv recommended)
This tool allows distributing energysums geographically. The Inputdata is provided by SpiceEV

## Run Tool
- you can define the regions in the File `regions.csv` in directory `Data`
- parameters for use case 1 and 4 can be set in `location_config.cfg`
- run main.py with the desired scenario
- results are created in main directory as a .csv file for each use case and each region

Four use cases are considered: 
- use case 1: public fast
- use case 2: public slow
- use case 3: private home
- use case 4: private work

