
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import configparser as cp
import os

import Use_Cases
import Utility

if __name__ == '__main__':

    print('Starting Program for Distribution of Energy...')

    # read config file
    cwd = os.getcwd()
    parser = cp.ConfigParser()
    cfg_file = os.path.join(cwd, 'location_config.cfg')
    if not os.path.isfile(cfg_file):
        raise FileNotFoundError(f'Config file {cfg_file} not found.')
    try:
        parser.read(cfg_file)
    except Exception:
        raise FileNotFoundError(f'Cannot read config file {cfg_file} - malformed?')
    csv_name = parser.get('region_mode', 'csv_name')
    uc1_radius = int(parser.get('uc_params', 'uc1_radius'))
    uc4_weight_retail = float(parser.get('uc_params', 'uc4_weight_retail'))
    uc4_weight_commercial = float(parser.get('uc_params', 'uc4_weight_commercial'))
    uc4_weight_industrial = float(parser.get('uc_params', 'uc4_weight_industrial'))

    region_data = Utility.load_csv(os.path.join('.', 'Data', csv_name))
    region_key = ['']*len(region_data)
    i = 0
    while i < len(region_data):  #TODO: rethink region data and csv
        region_key[i] = region_data.loc[i, 'AGS']
        i += 1

    anz_regions = len(region_key)
    print('Number of Regions set:', anz_regions)
    print('AGS Region_Key is set to:', region_key)

    # read input data
    fuel_stations = Utility.einlesen_geo(os.path.join('.', 'Data', 'fuel_stations.gpkg'))
    anz_fs = len(fuel_stations)

    boundaries = Utility.einlesen_geo(os.path.join('.', 'Data', 'boundaries.gpkg'))

    boundaries.set_index('ags_0', inplace=True)     # AGS als Index des Dataframes setzen
    boundaries = boundaries.dissolve(by='ags_0')    # Zusammenfassen der Regionenn mit geleichem AGS
    boundaries = boundaries.to_crs(3035)

    traffic = Utility.einlesen_geo(os.path.join('.', 'Data', 'berlin_verkehr.gpkg'))
    traffic = traffic.to_crs(3035)  # transform to reference Coordinate System

    zensus_data = Utility.einlesen_geo(
        os.path.join('.', 'Data', 'destatis_zensus_population_per_ha_filtered.gpkg'))
    zensus_data = zensus_data.to_crs(3035)
    zensus = zensus_data.iloc[:, 2:5]

    public = Utility.einlesen_geo(os.path.join('.', 'Data', 'osm_poi_elia.gpkg'))

    poi_data = Utility.load_csv(os.path.join('.', 'Data', '2020-12-02_OSM_POI_Gewichtung.csv'))
    poi = pd.DataFrame.from_dict(poi_data)

    work = Utility.einlesen_geo(os.path.join('.', 'Data', 'landuse.gpkg'))

    am_data = Utility.load_csv(os.path.join('.', 'Data', 'Res_SimBEV', 'amenity_update.csv'))
    amenities = pd.DataFrame.from_dict(am_data)
    anz_regions = len(boundaries)

    # Start the Use Cases for areas in region_key
    for key in region_key:
        region = boundaries.loc[key, 'geometry']
        region = gpd.GeoSeries(region)  # format to geoseries, otherwise problems plotting

        # Start Use Cases
        fs = Use_Cases.uc1_public_fast(fuel_stations, boundaries,
                                       amenities, traffic,
                                       region, key, uc1_radius)

        pu = Use_Cases.uc2_public_slow(public, boundaries,
                                       amenities, poi,
                                       region, key)

        pl = Use_Cases.uc3_private_home(zensus, boundaries,
                                        amenities, region,
                                        key)

        pw = Use_Cases.uc4_private_work(work, boundaries,
                                        amenities, region,
                                        key, uc4_weight_retail,
                                        uc4_weight_commercial, uc4_weight_industrial)

    plt.show()
