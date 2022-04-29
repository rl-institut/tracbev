import pandas as pd
import geopandas as gpd
import numpy as np
import configparser as cp
import argparse
from datetime import datetime
import pathlib

import usecase as uc


def parse_data(args):
    # read config file
    parser = cp.ConfigParser()
    scenario_path = pathlib.Path('scenarios', args.scenario)
    cfg_file = pathlib.Path(scenario_path, 'tracbev_config.cfg')
    data_dir = pathlib.Path('data')

    if not cfg_file.is_file():
        raise FileNotFoundError(f'Config file {cfg_file} not found.')
    try:
        parser.read(cfg_file)
    except Exception:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')

    run_hpc = parser.getboolean('use_cases', 'hpc')
    run_public = parser.getboolean('use_cases', 'public')
    run_home = parser.getboolean('use_cases', 'home')
    run_work = parser.getboolean('use_cases', 'work')

    # always used parameters
    boundaries = gpd.read_file(pathlib.Path(data_dir, parser.get('data', 'boundaries')))
    boundaries.set_index('ags_0', inplace=True)  # region key as dataframe index
    boundaries = boundaries.dissolve(by='ags_0')  # merge regions with identical key

    ts_path = pathlib.Path(scenario_path, "charging_timeseries")
    ts_dict = {}
    for ts in ts_path.glob("*.csv"):
        ts_dict[ts.stem] = pd.read_csv(ts, sep=",")

    charge_info_file = parser.get("uc_params", "charging_info")
    charge_info = pd.read_csv(pathlib.Path(data_dir, charge_info_file), sep=';', index_col="usecase")
    charge_info_dict = charge_info.to_dict(orient="index")

    num_regions = len(ts_dict)
    print('Number of Regions set:', num_regions)
    print('AGS Region_Key is set to:', ts_dict.keys())

    # set random seed from config or truly random if none is given
    rng_seed = parser['basic'].getint('random_seed', None)
    rng = np.random.default_rng(rng_seed)

    config_dict = {
        'boundaries': boundaries,
        'run_hpc': run_hpc,
        'run_public': run_public,
        'run_home': run_home,
        'run_work': run_work,
        'timeseries': ts_dict,
        'visual': parser.getboolean("basic", "plots"),
        'charge_info': charge_info_dict,
        'scenario_name': args.scenario,
        'random_seed': rng
    }

    if run_hpc:
        hpc_pos_file = parser.get('data', 'hpc_positions')
        positions = gpd.read_file(pathlib.Path(data_dir, hpc_pos_file))
        config_dict["hpc_points"] = positions

    if run_public:
        public_data_file = parser.get('data', 'public_poi')
        public_data = gpd.read_file(pathlib.Path(data_dir, public_data_file))
        public_pos_file = parser.get('data', 'public_positions')
        public_positions = gpd.read_file(pathlib.Path(data_dir, public_pos_file))
        config_dict.update({'poi_data': public_data, 'public_positions': public_positions})

    if run_home:
        zensus_data_file = parser.get('data', 'zensus_data')
        zensus_data = gpd.read_file(pathlib.Path(data_dir, zensus_data_file))
        zensus_data = zensus_data.to_crs(3035)

        simbev_meta = pd.read_json(pathlib.Path(ts_path, "metadata_simbev_run.json"))
        home_charging_prob = simbev_meta.loc["charging_probabilities", "config"]["private_charging_home"]

        num_car = simbev_meta.loc[:, "car_amounts"].dropna()

        config_dict.update({
            "sfh_available": parser.getfloat("uc_params", "single_family_home_share"),
            "sfh_avg_spots": parser.getfloat("uc_params", "single_family_home_spots"),
            "mfh_available": parser.getfloat("uc_params", "multi_family_home_share"),
            "mfh_avg_spots": parser.getfloat("uc_params", "multi_family_home_spots"),
            "zensus": zensus_data,
            "home_prob": float(home_charging_prob),
            "num_car": num_car
        })

    if run_work:
        work_retail = float(parser.get('uc_params', 'work_weight_retail'))
        work_commercial = float(parser.get('uc_params', 'work_weight_commercial'))
        work_industrial = float(parser.get('uc_params', 'work_weight_industrial'))
        work = gpd.read_file(pathlib.Path(data_dir, 'landuse.gpkg'))
        work_dict = {'retail': work_retail, 'commercial': work_commercial, 'industrial': work_industrial}
        config_dict.update({'work': work, 'work_dict': work_dict})

    return config_dict


def run_tracbev(data_dict):
    bounds = data_dict['boundaries']

    # create result directory
    timestamp_now = datetime.now()
    timestamp = timestamp_now.strftime("%y-%m-%d_%H%M%S")
    result_dir = pathlib.Path('results', '{}_{}'.format(data_dict['scenario_name'], timestamp))
    result_dir.mkdir(exist_ok=True, parents=True)

    for key, timeseries in data_dict['timeseries'].items():
        region = bounds.loc[key, 'geometry']
        region = gpd.GeoSeries(region)  # format to geo series, otherwise problems plotting

        data_dict.update({'result_dir': result_dir, 'region': region, 'key': key})
        # Start Use Cases
        if data_dict['run_hpc']:
            uc.hpc(data_dict['hpc_points'], data_dict)

        if data_dict['run_public']:
            uc.public(data_dict['public_positions'], data_dict['poi_data'],
                      data_dict)

        if data_dict['run_home']:
            uc.home(data_dict['zensus'],
                    data_dict, data_dict['home_prob'], data_dict['num_car'])

        if data_dict['run_work']:
            uc.work(data_dict['work'],
                    data_dict['work_dict'],
                    data_dict)


def main():
    print('Starting Program for Distribution of Energy...')

    argparser = argparse.ArgumentParser(description='TracBEV tool for allocation of charging infrastructure')
    argparser.add_argument('scenario', default="default_scenario", nargs='?',
                           help='Set name of the scenario directory')
    p_args = argparser.parse_args()

    data = parse_data(p_args)
    run_tracbev(data)


if __name__ == '__main__':
    main()
