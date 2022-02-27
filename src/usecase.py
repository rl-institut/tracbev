import plots
import utility
import pandas as pd
import geopandas as gpd
import math
import usecase_helpers


def hpc(hpc_points: gpd.GeoDataFrame,
        uc_dict, timestep=15):
    """
    Calculate placements and energy distribution for use case hpc.

    :param hpc_points: gpd.GeoDataFrame
        GeoDataFrame of possible hpc locations
    :param uc_dict: dict
        contains basic run info like region boundary and save directory
    :param timestep: int
        time step of the simbev input series, default: 15 (minutes)
    """
    uc_id = 'hpc'
    print('Use case: ', uc_id)

    # get hpc charging series
    load = uc_dict['timeseries'].loc[:, "sum hpc"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()
    charge_info = uc_dict["charge_info"][uc_id]
    num_hpc = math.ceil(load_peak / charge_info["avg_power"] * charge_info["c_factor"])

    if num_hpc > 0:
        # filter hpc points by region
        in_region_bool = hpc_points["geometry"].within(uc_dict["region"].loc[0])
        in_region = hpc_points.loc[in_region_bool].copy()
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
            sim_in_region_sorted = sim_in_region.sort_values("potential", ascending=False)
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
        uc_dict, timestep=15):
    """
    Calculate placements and energy distribution for use case hpc.

    :param public_points: gpd.GeoDataFrame
        existing public charging points
    :param public_data: gpd.GeoDataFrame
        clustered POI
    :param uc_dict: dict
        contains basic run info like region boundary and save directory
    :param timestep: int
        time step of the simbev input series, default: 15 (minutes)
    """

    uc_id = "public"
    print("Use case: " + uc_id)

    load = uc_dict['timeseries'].loc[:, "sum public"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    load_peak = load.max()
    charge_info = uc_dict["charge_info"][uc_id]
    num_public = math.ceil(load_peak / charge_info["avg_power"] * charge_info["c_factor"])
    if num_public > 0:
        # filter hpc points by region
        in_region_bool = public_points["geometry"].within(uc_dict["region"].loc[0])
        in_region = public_points.loc[in_region_bool].copy()
        poi_in_region_bool = public_data["geometry"].within(uc_dict["region"].loc[0])
        poi_in_region = public_data.loc[poi_in_region_bool].copy()
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


def home(
        home_data: gpd.GeoDataFrame,
        uc_dict, home_charge_prob, car_num, timestep=15):
    """
    Calculate placements and energy distribution for use case hpc.

    :param home_data: gpd.GeoDataFrame
        info about house types
    :param uc_dict: dict
        contains basic run info like region boundary and save directory
    :param home_charge_prob: float
        probability of privately available home charging
    :param car_num: pd.Series
        total cars per car type in scenario
    :param timestep: int
        time step of the simbev input series, default: 15 (minutes)
    """
    uc_id = "home"
    print("Use case: " + uc_id)

    load = uc_dict['timeseries'].loc[:, "sum home"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60
    num_home = math.ceil(car_num.sum() * home_charge_prob)

    if num_home > 0:
        # filter houses by region
        in_region_bool = home_data["geometry"].within(uc_dict["region"].loc[0])
        in_region = home_data.loc[in_region_bool].copy()
        in_region = in_region.sort_values(by="num", ascending=False)
        # TODO: allow multiple points per geopoint, increasing the energy
        # TODO rewrite apportion to fit home usecase (randomly distribute num_home depending on column num)
        potential = usecase_helpers.apportion_home(in_region, num_home)
        in_region["charge_spots"] = potential
        in_region = in_region.loc[in_region["charge_spots"] > 0]
        in_region["energy"] = energy_sum * in_region["charge_spots"] / num_home
        in_region = in_region.sort_values(by="energy", ascending=False)
        # in_region = in_region.iloc[:num_home]
        # in_region = in_region.assign(energy=energy_sum/num_home)
        # outputs
        print(energy_sum, "kWh got charged in region")
        if uc_dict["visual"]:
            plots.plot_uc(uc_id, in_region, uc_dict)
        cols = ["geometry", "charge_spots", "energy"]
        utility.save(in_region, uc_id, cols, uc_dict)


def work(
        landuse, weights_dict,
        uc_dict, timestep=15):
    """
    Calculate placements and energy distribution for use case hpc.

    :param landuse: gpd.GeoDataFrame
        work areas by land use
    :param weights_dict: dict
        weights for different land use types
    :param uc_dict: dict
        contains basic run info like region boundary and save directory
    :param timestep: int
        time step of the simbev input series, default: 15 (minutes)
    """
    uc_id = "work"
    print("Use case: " + uc_id)

    load = uc_dict["timeseries"].loc[:, "sum work"]
    load_sum = load.sum()
    energy_sum = load_sum * timestep / 60

    in_region_bool = landuse.within(uc_dict["region"].loc[0])
    in_region = landuse[in_region_bool].copy()
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
    cols = ["geometry", "landuse", "potential", "energy"]
    utility.save(result, uc_id, cols, uc_dict)
