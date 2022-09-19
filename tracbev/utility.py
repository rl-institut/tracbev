import os

import geopandas as gpd
import pandas as pd


def weights_to_dict(weights: pd.DataFrame):
    result = {}
    for i in weights.index:
        osm_key = weights.at[i, "OSM-Key"]
        osm_value = weights.at[i, "OSM-Value"]
        value = weights.at[i, "weight"]
        key = osm_key + ":" + osm_value
        result[key] = value
    return result


# save in .csv format
def save(data: gpd.GeoDataFrame, uc, col_select, uc_dict):
    region_key = uc_dict["key"]
    filename = "output_{}_{}".format(uc, region_key)
    save_path_csv = os.path.join(uc_dict["result_dir"], filename + ".csv")
    save_path_gpkg = os.path.join(uc_dict["result_dir"], filename + ".gpkg")
    data.reset_index(drop=True, inplace=True)
    data.to_csv(save_path_csv, sep=",", columns=col_select, decimal=".")
    data.to_file(save_path_gpkg, driver="GPKG")
    print("saving {} in region {} successful".format(uc, region_key))
