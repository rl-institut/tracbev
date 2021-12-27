
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import configparser as cp
import os

import use_cases as uc
import utility


def parse_data():
    # read config file
    cwd = os.getcwd()
    parser = cp.ConfigParser()
    cfg_file = os.path.join(cwd, 'tracbev_config.cfg')
    if not os.path.isfile(cfg_file):
        raise FileNotFoundError(f'Config file {cfg_file} not found.')
    try:
        parser.read(cfg_file)
    except Exception:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')

    csv_name = parser.get('region_mode', 'csv_name')
    run_uc1 = parser.getboolean('basic', 'uc1_hpc')
    run_uc2 = parser.getboolean('basic', 'uc2_public')
    run_uc3 = parser.getboolean('basic', 'uc3_home')
    run_uc4 = parser.getboolean('basic', 'uc4_work')

    # always used parameters
    boundaries = utility.einlesen_geo(os.path.join('.', 'Data', 'boundaries.gpkg'))
    boundaries.set_index('ags_0', inplace=True)  # AGS als Index des Dataframes setzen
    boundaries = boundaries.dissolve(by='ags_0')  # Zusammenfassen der Regionenn mit geleichem AGS
    boundaries = boundaries.to_crs(3035)

    am_data = utility.load_csv(os.path.join('.', 'Data', 'Res_SimBEV', 'amenity_update.csv'))
    amenities = pd.DataFrame.from_dict(am_data)

    region_data = utility.load_csv(os.path.join('.', 'Data', csv_name))
    region_key = [''] * len(region_data)
    i = 0
    while i < len(region_data):  # TODO: rethink region data and csv
        region_key[i] = region_data.loc[i, 'AGS']
        i += 1

    anz_regions = len(region_key)
    print('Number of Regions set:', anz_regions)
    print('AGS Region_Key is set to:', region_key)

    config_dict = {
        'boundaries': boundaries,
        'amenities': amenities,
        'region_key': region_key,
        'run_uc1': run_uc1,
        'run_uc2': run_uc2,
        'run_uc3': run_uc3,
        'run_uc4': run_uc4,
    }

    if run_uc1:
        uc1_radius = int(parser.get('uc_params', 'uc1_radius'))
        fuel_stations = utility.einlesen_geo(os.path.join('.', 'Data', 'fuel_stations.gpkg'))
        traffic = utility.einlesen_geo(os.path.join('.', 'Data', 'berlin_verkehr.gpkg'))
        traffic = traffic.to_crs(3035)  # transform to reference Coordinate System
        config_dict.update({'uc1_radius': uc1_radius, 'fuel_stations': fuel_stations, 'traffic': traffic})

    if run_uc2:
        public = utility.einlesen_geo(os.path.join('.', 'Data', 'osm_poi_elia.gpkg'))

        poi_data = utility.load_csv(os.path.join('.', 'Data', '2020-12-02_OSM_POI_Gewichtung.csv'))
        poi = pd.DataFrame.from_dict(poi_data)
        config_dict.update({'public': public, 'poi': poi})

    if run_uc3:
        zensus_data = utility.einlesen_geo(
            os.path.join('.', 'Data', 'destatis_zensus_population_per_ha_filtered.gpkg'))
        zensus_data = zensus_data.to_crs(3035)
        zensus = zensus_data.iloc[:, 2:5]
        config_dict['zensus'] = zensus

    if run_uc4:
        uc4_weight_retail = float(parser.get('uc_params', 'uc4_weight_retail'))
        uc4_weight_commercial = float(parser.get('uc_params', 'uc4_weight_commercial'))
        uc4_weight_industrial = float(parser.get('uc_params', 'uc4_weight_industrial'))
        work = utility.einlesen_geo(os.path.join('.', 'Data', 'landuse.gpkg'))
        config_dict.update({'retail': uc4_weight_retail, 'commercial': uc4_weight_commercial,
                            'industrial': uc4_weight_industrial, 'work': work})

    return config_dict


if __name__ == '__main__':

    print('Starting Program for Distribution of Energy...')
    data = parse_data()
    bounds = data['boundaries']
    amens = data['amenities']

    # create result folder
    if not os.path.exists('results'):
        os.makedirs('results')

    for key in data['region_key']:
        region = bounds.loc[key, 'geometry']
        region = gpd.GeoSeries(region)  # format to geo series, otherwise problems plotting

        # Start Use Cases
        if data['run_uc1']:
            fs = uc.uc1_hpc(data['fuel_stations'], bounds,
                            amens, data['traffic'],
                            region, key, data['uc1_radius'])

        if data['run_uc2']:
            pu = uc.uc2_public(data['public'], bounds,
                               amens, data['poi'],
                               region, key)

        if data['run_uc3']:
            pl = uc.uc3_home(data['zensus'], bounds,
                             amens, region,
                             key)

        if data['run_uc4']:
            pw = uc.uc4_work(data['work'], bounds,
                             amens, region,
                             key, data['retail'],
                             data['commercial'], data['industrial'])

    plt.show()
