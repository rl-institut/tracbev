import plots
import utility
import pandas as pd
import numpy as np
import geopandas as gpd
import math
import usecase_helpers


def hpc(hpc_points: gpd.GeoDataFrame,
        uc_dict, min_power=150, timestep=15):
    """
    Calculate placements and energy distribution for use case hpc.

    :param hpc_points:
        GeoDataFrame of possible hpc locations
    :param uc_dict:
        Contains basic run info like region boundary and save directory
    :param min_power:
        used to calculate needed charging points, default 150
    :param timestep:
        timestep of charging_series, default 15
    """
    uc_id = 'hpc'
    print('Use case: ', uc_id)

    # get hpc charging series
    load = uc_dict['timeseries'].loc[:, "sum hpc"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()
    num_hpc = math.ceil(load_peak / min_power)

    if num_hpc > 0:
        # filter hpc points by region
        in_region_bool = hpc_points["geometry"].within(uc_dict["region"].loc[0])
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
        if uc_dict["visual"]:
            plots.plot_uc(uc_id, real_in_region, uc_dict)
        cols.remove("new_hpc_tag")
        cols.append("share")
        utility.save(real_in_region, uc_id, cols, uc_dict)
    else:
        print("No hpc charging in timeseries")


def public(
        public_points: gpd.GeoDataFrame, public_data: gpd.GeoDataFrame,
        uc_dict, timestep=15, avg_power=11):

    uc_id = "public"
    print("Use case: " + uc_id)

    load = uc_dict['timeseries'].loc[:, "sum public"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()
    num_public = math.ceil(load_peak / avg_power)
    if num_public > 0:
        # filter hpc points by region
        in_region_bool = public_points["geometry"].within(uc_dict["region"].loc[0])
        in_region = public_points.loc[in_region_bool]
        poi_in_region_bool = public_data["geometry"].within(uc_dict["region"].loc[0])
        poi_in_region = public_data.loc[poi_in_region_bool]
        num_public_real = in_region["count"].sum()
        # match with clusters anyway (for weights)
        region_points, region_poi = usecase_helpers.match_existing_points(in_region, poi_in_region)

        if num_public_real < num_public:
            additional_public = num_public - num_public_real
            # distribute additional public points via POI
            add_points = usecase_helpers.distribute_by_poi(region_poi, additional_public)
            region_points = pd.concat(region_points, add_points)

        region_points["energy"] = region_points["potential"] / region_points["potential"].sum() * energy_sum

        # outputs
        print(energy_sum, "kWh got charged in region")
        if uc_dict["visual"]:
            plots.plot_uc(uc_id, region_points, uc_dict)
        cols = ["geometry", "potential", "energy"]
        utility.save(region_points, uc_id, cols, uc_dict)

    else:
        print("No public charging in timeseries")


def home_old(
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


def work(
        landuse, weights_dict,
        uc_dict, timestep=15):
    uc_id = "work"
    print("Use case: " + uc_id)

    load = uc_dict["timeseries"].loc[:, "sum work"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()

    in_region_bool = landuse.within(uc_dict["region"].loc[0])
    in_region = landuse[in_region_bool]
    # calculating the area of polygons
    in_region["area"] = in_region['geometry'].area / 10 ** 6
    groups = in_region.groupby("landuse")
    group_labels = ["retail", "commercial", "industrial"]
    result = gpd.GeoDataFrame(columns=["geometry", "landuse", "potential"])
    for g in group_labels:
        group = groups.get_group(g)
        group = group.assign(potential=group["geometry"].area * weights_dict[g])
        result = gpd.GeoDataFrame(pd.concat([result, group]), crs="EPSG:3035")

    result['energy'] = result['potential'] * energy_sum / result['potential'].sum()
    # outputs
    print(energy_sum, "kWh got charged in region")
    if uc_dict["visual"]:
        plots.plot_uc(uc_id, result, uc_dict)
    # TODO check cols
    cols = ["geometry", "landuse", "potential", "energy"]
    utility.save(result, uc_id, cols, uc_dict)


def work_old(work_data,
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
