import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import configparser as cp
import os
import argparse
from datetime import datetime

import usecase as uc
import utility


def parse_data(args):
    # read config file
    cwd = os.getcwd()
    parser = cp.ConfigParser()
    cfg_file = os.path.join(cwd, 'scenarios', args.config)
    data_dir = os.path.join(cwd, 'data')

    if not os.path.isfile(cfg_file):
        raise FileNotFoundError(f'Config file {cfg_file} not found.')
    try:
        parser.read(cfg_file)
    except Exception:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')

    region_csv = parser.get('data', 'region_csv')
    timeseries_csv = parser.get('data', 'timeseries_csv')
    timeseries_format = parser.get('data', 'timeseries_format')
    sep_dict = {'simbev': ',', 'spiceev': ';'}
    run_hpc = parser.getboolean('use_cases', 'hpc')
    run_public = parser.getboolean('use_cases', 'public')
    run_home = parser.getboolean('use_cases', 'home')
    run_work = parser.getboolean('use_cases', 'work')
    visual = parser.getboolean("basic", "plots")

    # always used parameters
    boundaries = gpd.read_file(os.path.join(data_dir, 'boundaries.gpkg'))
    boundaries.set_index('ags_0', inplace=True)  # AGS als Index des Dataframes setzen
    boundaries = boundaries.dissolve(by='ags_0')  # Zusammenfassen der Regionenn mit geleichem AGS
    boundaries = boundaries.to_crs(3035)

    timeseries = pd.read_csv(os.path.join(data_dir, 'charging_timeseries', timeseries_csv),
                             sep=sep_dict[timeseries_format])

    # TODO: use pandas?
    region_data = utility.load_csv(os.path.join(data_dir, region_csv))
    region_key = [''] * len(region_data)
    i = 0
    while i < len(region_data):  # TODO: rethink region data and csv
        region_key[i] = region_data.loc[i, 'AGS']
        i += 1

    num_regions = len(region_key)
    print('Number of Regions set:', num_regions)
    print('AGS Region_Key is set to:', region_key)

    uc_dict = {
        'timeseries': timeseries,
        'region_key': region_key,
        'visual': visual
    }

    config_dict = {
        'boundaries': boundaries,
        'run_hpc': run_hpc,
        'run_public': run_public,
        'run_home': run_home,
        'run_work': run_work,
        'uc_dict': uc_dict
    }

    if run_hpc:
        hpc_pos_file = parser.get('data', 'hpc_positions')
        positions = gpd.read_file(os.path.join(data_dir, hpc_pos_file))
        config_dict["hpc_points"] = positions

    if run_public:
        public_data = gpd.read_file(os.path.join(data_dir, 'osm_poi_elia.gpkg'))
        public_pos_file = parser.get('data', 'public_positions')
        public_positions = gpd.read_file(os.path.join(data_dir, public_pos_file))
        poi_weights = pd.read_csv(os.path.join(data_dir, 'poi_weights.csv'), sep=';', encoding='mbcs')
        weights_dict = utility.weights_to_dict(poi_weights)
        config_dict.update({'poi_data': public_data, 'poi_weights': weights_dict, 'public_positions': public_positions})

    if run_home:
        zensus_data = gpd.read_file(
            os.path.join(data_dir, 'zensus.gpkg'))
        zensus_data = zensus_data.to_crs(3035)
        zensus = zensus_data.iloc[:, 2:5]
        config_dict['zensus'] = zensus

    if run_work:
        work_retail = float(parser.get('uc_params', 'work_weight_retail'))
        work_commercial = float(parser.get('uc_params', 'work_weight_commercial'))
        work_industrial = float(parser.get('uc_params', 'work_weight_industrial'))
        work = gpd.read_file(os.path.join(data_dir, 'landuse.gpkg'))
        work_dict = {'retail': work_retail, 'commercial': work_commercial, 'industrial': work_industrial}
        config_dict.update({'work': work, 'work_dict': work_dict})

    return config_dict


def run_tracbev(data_dict):
    bounds = data_dict['boundaries']

    # create result directory
    timestamp_now = datetime.now()
    timestamp = timestamp_now.strftime("%y-%m-%d_%H%M%S")
    result_dir = os.path.join('results', 'tracbev_{}'.format(timestamp))
    os.makedirs(result_dir, exist_ok=True)
    run_dict = data_dict['uc_dict']

    for key in run_dict['region_key']:
        region = bounds.loc[key, 'geometry']
        region = gpd.GeoSeries(region)  # format to geo series, otherwise problems plotting

        run_dict.update({'result_dir': result_dir, 'region': region, 'key': key})
        # Start Use Cases
        if data_dict['run_hpc']:
            uc.hpc(data_dict['hpc_points'], run_dict)

        if data_dict['run_public']:
            uc.public(data_dict['public_positions'], data_dict['poi_data'],
                      run_dict)

        if data_dict['run_home']:
            pl = uc.home(data_dict['zensus'],
                         run_dict)

        if data_dict['run_work']:
            uc.work(data_dict['work'],
                    data_dict['work_dict'],
                    run_dict)


def main():
    print('Starting Program for Distribution of Energy...')

    argparser = argparse.ArgumentParser(description='TracBEV tool for allocation of charging infrastructure')
    argparser.add_argument('config', default="tracbev_config.cfg", nargs='?',
                           help='Set the config which is located in ./scenarios .')
    p_args = argparser.parse_args()

    data = parse_data(p_args)
    run_tracbev(data)
    plt.show()


if __name__ == '__main__':
    main()
