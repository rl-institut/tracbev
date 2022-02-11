import plots
import utility
import pandas as pd
import numpy as np
import geopandas as gpd
import math


def hpc(hpc_points: gpd.GeoDataFrame, charging_series: pd.DataFrame,
        region, region_key, dir_result, min_power=150, timestep=15):
    uc_id = 'hpc'
    print('Use case: ', uc_id)

    # get hpc charging series
    load = charging_series.loc[:, "sum hpc"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()
    num_hpc = math.ceil(load_peak / min_power)

    if num_hpc > 0:
        # filter hpc points by region
        in_region_bool = hpc_points["geometry"].within(region.loc[0])
        in_region = hpc_points.loc[in_region_bool]
        if "has_hpc" in in_region.columns:
            in_region = in_region.loc[in_region["has_hpc"]]
        cols = ["geometry", "hpc_count", "potential", "new_hpc_index", "new_hpc_tag"]
        in_region = in_region[cols]
        # select all hpc points tagged 0, all registered points
        real_mask = in_region["new_hpc_tag"] == 0
        real_in_region = in_region.loc[real_mask]
        num_hpc_real = real_in_region["hpc_count"].sum()

        if num_hpc_real < num_hpc:
            sim_in_region = in_region.loc[~real_mask]
            sim_in_region = sim_in_region.loc[in_region["new_hpc_index"] > 0]
            sim_in_region_sorted = sim_in_region.sort_values("potential")
            additional_hpc = int(min(num_hpc - num_hpc_real, len(sim_in_region.index)))
            selected_hpc = sim_in_region_sorted.iloc[:additional_hpc]
            real_in_region = real_in_region.append(selected_hpc)

        total_potential = real_in_region["potential"].sum()
        real_in_region = real_in_region.assign(share=real_in_region["potential"] / total_potential).round(6)

        # outputs
        print(energy_sum, "kWh got fastcharged in region")
        plots.plot_uc(uc_id, real_in_region, region, dir_result)
        cols.remove("new_hpc_tag")
        cols.append("share")
        utility.save(real_in_region, uc_id, cols, region_key, dir_result)
    else:
        print("No hpc in charging timeseries")


def public(
        public_data,
        timeseries, poi,
        region, region_key, dir_result):

    print('Use case: public')
    uc_id = 'public'

    # get poi's in region
    public_in_region_bool = pd.Series(public_data.geometry.within(region.loc[0]), name='Bool')
    public_in_region = public_data.join(public_in_region_bool)
    pir = public_in_region.loc[public_in_region['Bool'] == 1]   # pir = public in region

    anz_pir = len(pir)
    data = np.zeros(anz_pir, )
    es = pd.Series(data, name='energysum')
    pir = pir.join(es)

    # take all columns from simbev output that are part of the public usecase
    cols_public = timeseries.columns[-7:-2]
    load_power = timeseries[cols_public].sum(axis=1)
    load_power.name = 'chargepower_public'
    load_power = pd.to_numeric(load_power)
    energy_sum = load_power * 15 / 60  # Ladeleistung in Energie umwandeln TODO: get timestep from simbev run metadata

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

    plots.plot_public(pir, region)

    col_select = ['name', 'amenity', 'leisure', 'shop', 'tourism',
                  'geometry', 'energysum', 'weight', 'conversionfactor']
    utility.save(pir, uc_id, col_select, region_key, dir_result)


def home(
        zensus,
        timeseries, region,
        region_key, dir_result):

    print('Use case: home')
    uc_id = 'home'

    # getting zenusdata in region
    home_in_region_bool = pd.Series(zensus.geometry.within(region.loc[0]), name='Bool')
    home_in_region = zensus.join(home_in_region_bool)
    hir = home_in_region.loc[home_in_region['Bool'] == 1]   # hir = home in region

    anz_hir = len(hir)
    data = np.zeros(anz_hir, )
    es = pd.Series(data, name='energysum')
    hir = hir.join(es)
    hir['energysum'] = np.nan

    load_power = timeseries.loc[:, 'sum UC home']
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

    plots.plot_home(hir, region)

    col_select = ['population', 'geom_point', 'geometry', 'energysum', 'conversionfactor']
    utility.save(hir, uc_id, col_select, region_key, dir_result)

    return zensus


def work(work_data,
         timeseries, region,
         region_key, weight_retail,
         weight_commercial, weight_industrial, dir_result):

    print('Use case: work')
    uc_id = 'work'

    # getting pois of area
    work_in_region_bool = pd.Series(work_data.geometry.within(region.loc[0]), name='Bool')
    work_in_region = work_data.join(work_in_region_bool)
    wir = work_in_region.loc[work_in_region['Bool'] == 1]  # wir = work in region

    anz_wir = len(wir)
    data = np.zeros(anz_wir, )
    es = pd.Series(data, name='energysum')
    wir = wir.join(es)
    wir['energysum'] = np.nan

    load_power = timeseries.loc[:, 'sum UC work']
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

    plots.plot_work(wir, region)

    col_select = ['landuse', 'geometry', 'center_geo', 'energysum', 'weight', 'conversionfactor']
    utility.save(wir, uc_id, col_select, region_key, dir_result)
