import geopandas as gpd
import pandas as pd


# used in preprocessing only
def poi_value(poi_data, weights):
    result = 0
    cols = ["amenity", "leisure", "shop", "tourism"]
    for col in cols:
        if poi_data[col] is not None:
            key = col + ":" + poi_data[col]
            if key in weights:
                result = max(result, weights[key])
            else:
                print(key, "not in weights csv")
    return result


# used in preprocessing only
def poi_cluster(poi_data, max_radius, max_weight, increment):
    coords = []
    weights = []
    areas = []
    while len(poi_data):
        radius = increment
        weight = 0
        # take point of first row
        coord = poi_data.iat[0, 0]
        condition = True
        while condition:
            # create radius circle around point
            area = coord.buffer(radius)
            # select all POI within circle
            in_area_bool = poi_data["geometry"].within(area)
            in_area = poi_data.loc[in_area_bool]
            weight = in_area["weight"].sum()
            radius += increment
            condition = radius <= max_radius and weight <= max_weight

        # calculate combined weight
        coords.append(coord)
        weights.append(weight)
        areas.append(radius - increment)
        # delete all used points from poi data
        poi_data = poi_data.drop(in_area.index.tolist())
        print(len(poi_data))
    # create cluster geodataframe
    result_dict = {"geometry": coords, "potential": weights, "radius": areas}

    return gpd.GeoDataFrame(result_dict, crs="EPSG:3035")


# used in preprocessing only
def preprocess_poi(region_poi, weights, max_radius, max_weight, increment):
    # give POIs in region a value
    region_poi["weight"] = region_poi.apply(poi_value, args=(weights,), axis=1)
    region_poi = region_poi[["geometry", "weight"]]
    region_poi.sort_values("weight", inplace=True, ascending=False)
    # cluster POIs in close proximity
    return poi_cluster(region_poi, max_radius, max_weight, increment)


def distribute_by_poi(
        region_points: gpd.GeoDataFrame, region_poi: gpd.GeoDataFrame,
        weights, num_points):
    # merge cluster info with existing points (total weight of cluster)
    region_poi["exists"] = False
    for i in region_points.index:
        cluster = region_poi.contains(region_points.loc[i, "geometry"])
        cluster.loc[cluster, "exists"] = True
    # sort clusters without existing points by weight, then choose highest
    region_poi.sort_values("weight", inplace=True, ascending=False)
    mask = cluster.loc[:, "exists"]
    region_poi_exists = cluster[mask]
    region_poi_available = cluster[~mask]
    num_points = int(min(num_points, len(region_poi_available.index)))
    selected_hpc = region_poi_available.iloc[:num_points]
    result = gpd.GeoDataFrame(pd.concat([region_poi_exists, selected_hpc], ignore_index=True), crs="EPSG:3035")
    # choose point in cluster thats closest to big street
    return result
