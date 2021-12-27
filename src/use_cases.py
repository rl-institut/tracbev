import plots
import utility
import pandas as pd
import numpy as np


def uc1_hpc(
        fuel_stations, boundaries,
        amenities, traffic_data,
        region, region_key, radius):

    uc_id = 'Use_Case_1_Public_Fast'
    # radius = 900  # radius around fuel station for traffic acquisition

    # get fuelstations in region
    anz_fuel_stations = len(fuel_stations)
    fuel_in_region_bool = pd.Series(fuel_stations.geometry.within(boundaries.geometry[region_key]), name='Bool')
    fuel_stations = fuel_stations.join(fuel_in_region_bool)

    # add empty column for Traffic
    data = np.zeros(anz_fuel_stations)
    traffic = pd.Series(data, name='traffic')
    fuel_stations = fuel_stations.join(traffic)

    # locate fuelstations in region
    fs = fuel_stations.loc[fuel_stations['Bool'] == 1]

    x = np.arange(0, len(fs))
    fs = fs.assign(INDEX=x)
    fs.set_index('INDEX', inplace=True)

    # Calculating distribution Weights for Fuel Stations
    circles = fs.buffer(radius)

    anz_fs = len(fs)

    # Loop for calculating weight by using the appr. daily Traffic around Fuel Station
    i = 0
    while i < anz_fs:
        # Trafficdata inside a radius of 900 around Fuel Station
        traffic_around_fs = pd.Series(traffic_data.geometry.within(circles.geometry.iloc[i]), name='Bool')
        traffic_bool = traffic_data.join(traffic_around_fs)
        traffic_around_fs_true = traffic_data.loc[traffic_bool['Bool'] == 1]
        traffic_sum = traffic_around_fs_true['dtv'].sum()
        fs.iloc[i, 4] = traffic_sum

        i += 1

    anz_fs = len(fs)

    # Distribution of Energy
    if anz_fs > 0:
        data = np.zeros(anz_fs,)
        energy_sum_per_fs = pd.Series(data, name='energysum')
        fs = fs.join(energy_sum_per_fs)

        load_power = amenities.loc[:, 'sum UC hub']  # TODO use all sum columns
        load_power.name = 'loadpower_hpc'
        load_power = pd.to_numeric(load_power)
        energy_sum = load_power*15/60  # Ladeleistung in Energie umwandeln

        energy_sum_overall = energy_sum.sum()
        print(energy_sum_overall, 'kWh got fastcharged in region ', region_key)

        # sort descending by traffic
        fs = fs.sort_values(by=['traffic'], ascending=False)

        x = np.arange(0, len(fs))
        fs = fs.assign(INDEX=x)
        fs.set_index('INDEX', inplace=True)

        fs['energysum'] = utility.apportion(fs['traffic'], energy_sum_overall)
        fs['conversionfactor'] = fs['energysum'] / energy_sum_overall

    else:
        print('No fast charging possible, because no fuel station in the area!')
    if anz_fs != 0:
        plots.plot_uc1(fs, region,
                       traffic_data, circles)

    col_select = ['geometry', 'traffic', 'energysum', 'conversionfactor']
    utility.save(fs, uc_id, col_select, region_key)

    return fs


def uc2_public(
        public, boundaries,
        amenities, poi,
        region, region_key):

    print('UC2')
    uc_id = 'Use_Case_2_Public_Slow'

    # get poi's in region
    public_in_region_bool = pd.Series(public.geometry.within(boundaries.geometry[region_key]), name='Bool')
    public_in_region = public.join(public_in_region_bool)
    pir = public_in_region.loc[public_in_region['Bool'] == 1]   # pir = public in region

    anz_pir = len(pir)
    data = np.zeros(anz_pir, )
    es = pd.Series(data, name='energysum')
    pir = pir.join(es)

    load_power = amenities.loc[:, 'sum UC leisure']
    load_power.name = 'chargepower_public'
    load_power = pd.to_numeric(load_power)
    energy_sum = load_power * 15 / 60  # Ladeleistung in Energie umwandeln

    energy_sum_overall = energy_sum.sum()
    print(energy_sum_overall, 'kWh got charged at public space in region', region_key)

    # distribution of energysum based on weight of poi
    anz_pir = len(pir)
    pir['newindex'] = np.arange(anz_pir)
    pir.set_index('newindex', inplace=True)
    data = np.zeros(anz_pir)
    pir['weight'] = pd.Series(data)

    a = pir['amenity']
    le = pir['leisure']
    s = pir['shop']
    t = pir['tourism']

    # extract pois by Key
    poia = poi.loc[poi['OSM-Key'] == 'amenity']
    poil = poi.loc[poi['OSM-Key'] == 'leisure']
    pois = poi.loc[poi['OSM-Key'] == 'shop']

    # combining POI-data and geopackage
    i = 0
    while i <= anz_pir - 1:
        if a.iloc[i] is not None and a.iloc[i] in poia['OSM-Value'].values:
            data = poia.loc[poi['OSM-Value'] == a.iloc[i], "weight"]
            pir.iloc[i, 8] = data
        elif le.iloc[i] is not None and le.iloc[i] in poil['OSM-Value'].values:
            data = poil.loc[poi['OSM-Value'] == le.iloc[i], "weight"]
            pir.iloc[i, 8] = data
        elif s.iloc[i] is not None and s.iloc[i] in pois['OSM-Value'].values:
            data = pois.loc[poi['OSM-Value'] == s.iloc[i], "weight"]
            pir.iloc[i, 8] = data
        elif t.iloc[i] is not None and t.iloc[i] in poi['OSM-Value'].values:
            pir.iloc[i, 8] = 0
        else:
            pir.iloc[i, 8] = 0
            print('Missing OSM Key in Geopackage-Data for UC2')
        i += 1

    pir['weight'] = pd.to_numeric(pir['weight'], errors='coerce')

    x = np.arange(0, len(pir))
    pir = pir.assign(INDEX=x)
    pir.set_index('INDEX', inplace=True)

    pir['energysum'] = utility.apportion(pir['weight'], energy_sum_overall)
    pir['conversionfactor'] = pir['energysum'] / energy_sum_overall

    plots.plot_uc2(pir, region)

    col_select = ['name', 'amenity', 'leisure', 'shop', 'tourism',
                  'geometry', 'energysum', 'weight', 'conversionfactor']
    utility.save(pir, uc_id, col_select, region_key)


def uc3_home(
        zensus, boundaries,
        amenities, region,
        region_key):

    print('UC3')
    uc_id = 'Use_Case_3_Private_Home'

    # getting zenusdata in region
    home_in_region_bool = pd.Series(zensus.geometry.within(boundaries.geometry[region_key]), name='Bool')
    home_in_region = zensus.join(home_in_region_bool)
    hir = home_in_region.loc[home_in_region['Bool'] == 1]   # hir = home in region

    anz_hir = len(hir)
    data = np.zeros(anz_hir, )
    es = pd.Series(data, name='energysum')
    hir = hir.join(es)
    hir['energysum'] = np.nan

    load_power = amenities.loc[:, 'sum UC home']
    load_power.name = 'chargepower_home'
    load_power = pd.to_numeric(load_power)
    energy_sum = load_power * 15 / 60  # Ladeleistung in Energie umwandeln

    energy_sum_overall = energy_sum.sum()
    print(energy_sum_overall, 'kWh got charged at home in region', region_key)

    # distribution of energysum based on population in 100x100 area
    pop_in_area = sum(hir['population'])

    hir = hir.sort_values(by=['population'], ascending=False)

    hir['conversionfactor'] = home_in_region['population'] / pop_in_area

    x = np.arange(0, len(hir))
    hir = hir.assign(INDEX=x)
    hir.set_index('INDEX', inplace=True)

    hir['energysum'] = utility.apportion(hir['conversionfactor'], energy_sum_overall)

    plots.plot_uc3(hir, region)

    col_select = ['population', 'geom_point', 'geometry', 'energysum', 'conversionfactor']
    utility.save(hir, uc_id, col_select, region_key)

    return zensus


def uc4_work(work, boundaries,
             amenities, region,
             region_key, weight_retail,
             weight_commercial, weight_industrial):

    print('UC4')
    uc_id = 'Use_Case_4_Private_Work'

    # getting pois of area
    work_in_region_bool = pd.Series(work.geometry.within(boundaries.geometry[region_key]), name='Bool')
    work_in_region = work.join(work_in_region_bool)
    wir = work_in_region.loc[work_in_region['Bool'] == 1]  # wir = work in region

    anz_wir = len(wir)
    data = np.zeros(anz_wir, )
    es = pd.Series(data, name='energysum')
    wir = wir.join(es)
    wir['energysum'] = np.nan

    load_power = amenities.loc[:, 'sum UC work']
    load_power.name = 'chargepower_work'
    load_power = pd.to_numeric(load_power)
    energy_sum = load_power * 15 / 60  # convert power to energy

    energy_sum_overall = energy_sum.sum()
    print(energy_sum_overall, 'kWh got charged at work in region', region_key)

    # distribution of energysum based on area of Polygon
    anz_wir = len(wir)
    wir['newindex'] = np.arange(anz_wir)
    wir.set_index('newindex', inplace=True)
    data = np.zeros(anz_wir)
    wir['weight'] = pd.Series(data)

    # calculating the area of polygons
    area = wir['geometry'].area / 10 ** 6
    sum_area = sum(area)

    # calculation of weight for type of use
    i = 0
    while i <= anz_wir - 1:
        if 'retail' in wir.iloc[i, 0]:
            wir.iloc[i, 4] = weight_retail * area[i] / sum_area  # Weight for retail

        elif 'commercial' in wir.iloc[i, 0]:
            wir.iloc[i, 4] = weight_commercial * area[i] / sum_area  # Weight for commercial

        elif 'industrial' in wir.iloc[i, 0]:
            wir.iloc[i, 4] = weight_industrial * area[i] / sum_area  # Weight for industrial
        else:
            print('no specification')

        i += 1

    x = np.arange(0, len(wir))
    wir = wir.assign(INDEX=x)
    wir.set_index('INDEX', inplace=True)

    wir['energysum'] = utility.apportion(wir['weight'], energy_sum_overall)
    wir['conversionfactor'] = wir['energysum']/energy_sum_overall

    wir['center_geo'] = wir.centroid

    plots.plot_uc4(wir, region)

    col_select = ['landuse', 'geometry', 'center_geo', 'energysum', 'weight', 'conversionfactor']
    utility.save(wir, uc_id, col_select, region_key)
