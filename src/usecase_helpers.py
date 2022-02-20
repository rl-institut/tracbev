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
def preprocess_poi(region_poi_unfiltered, boundaries, weights, max_radius, max_weight, increment):
    # give POIs in region a value
    result = gpd.GeoDataFrame(["geometry", "weight"], crs="EPSG:3035")
    for i in boundaries.index:
        print("boundary index:", i)
        region_poi = region_poi_unfiltered.within(boundaries.at[i, "geometry"])
        if len(region_poi.index) > 0:
            region_poi["weight"] = region_poi.apply(poi_value, args=(weights,), axis=1)
            region_poi = region_poi[["geometry", "weight"]]
            region_poi.sort_values("weight", inplace=True, ascending=False)
            region_poi = poi_cluster(region_poi, max_radius, max_weight, increment)
            result = gpd.GeoDataFrame(pd.concat([result, region_poi]), crs="EPSG:3035")
    # cluster POIs in close proximity
    return result


def match_existing_points(
        region_points: gpd.GeoDataFrame, region_poi: gpd.GeoDataFrame):

    region_poi["exists"] = False
    poi_buffer = region_poi.buffer(region_poi["radius"])
    region_points["potential"] = 0
    for i in region_points.index:
        lis_point = region_points.at[i, "geometry"]
        cluster = poi_buffer.contains(lis_point)
        clusters = region_poi.loc[cluster]
        num_clusters = len(clusters.index)

        if num_clusters == 0:
            # TODO choose appropriate fallback value
            region_points.at[i, "potential"] = 0
        elif num_clusters == 1:
            # region_poi.loc[cluster, "exists"] = True
            region_points.at[i, "potential"] = clusters["potential"]
            region_poi.loc[cluster, "potential"] = True

        elif num_clusters > 1:
            # choose cluster with closest Point
            dist = clusters.distance(lis_point)
            idx = dist.idxmin()
            region_poi.at[idx, "exists"] = True
            region_points.at[i, "potential"] = clusters.at[idx, "potential"]

    # delete all clusters with exists = True
    region_poi = region_poi.loc[~region_poi["exists"]]

    return region_points, region_poi


def distribute_by_poi(
        region_poi: gpd.GeoDataFrame,
        num_points):
    # sort clusters without existing points by weight, then choose highest
    region_poi.sort_values("weight", inplace=True, ascending=False)
    num_points = int(min(num_points, len(region_poi.index)))
    selected_hpc = region_poi.iloc[:num_points]
    # choose point in cluster thats closest to big street
    return selected_hpc
