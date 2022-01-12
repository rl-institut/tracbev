import csv
import geopandas as gpd
import pandas as pd
import os


# load data from csv
def load_csv(file, delimiter=';', is_num=False, is_dict=False):
    data = {} if is_dict else []
    with open(file, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=delimiter)
        header = next(csv_reader)  # read header
        for row in csv_reader:
            # get entry (key) of row
            # key = row.pop(0)
            # convert values to numbers
            if is_num:
                row = [float(d) for d in row]
            # single value in row
            if len(row) == 1:
               row = row[0]
            # save values
            # if is_dict:
            #   data[key] = row
            else:
                data.append(row)
        data = pd.DataFrame(data, columns=header)
    return data


# save in .csv format
def save(data: pd.DataFrame, uc, col_select, region_key, save_dir):

    filename = 'output_geo_{}_region_{}.csv'.format(uc, region_key)
    path = os.path.join(save_dir, filename)
    data.to_csv(path, sep=';', columns=col_select, decimal=',', index=True)
    print('saving {} in region {} successful'.format(uc, region_key))


# distribution function
def apportion(weights, num_portions, cutoff=1):

    if cutoff > num_portions:
        print("cutoff too high")
        cutoff = 1
    if cutoff < 1:
        cutoff = 1  # would not finish otherwise

    assert(sum(weights) != 0)   # avoid div0

    q = num_portions / sum(weights)
    distribution = pd.Series([0 if (w*q) < cutoff else int(w * q) for w in weights])
    remaining = num_portions - sum(distribution)

    assert(remaining >= 0)  # just in case

    # Give remaining portions to bins with biggest fractional remainder.

    # annotate distribution with index
    indexlist = list(range(len(distribution)))

    # sort by biggest fractional remainder
    # cutoff: ignore empty bins
    indexlist.sort(key=lambda x: weights[x] * q - distribution[x], reverse=True)

    # increment bins with biggest remainder
    i = 0
    while remaining > 0:
        index = indexlist[i % len(distribution)]     # start again after traversing list once
        if distribution[index] >= cutoff:
            # already above cutoff: increase by one
            distribution[index] += 1
            remaining -= 1
        elif remaining >= cutoff:
            # below cutoff: increase to threshold
            distribution[index] += cutoff
            remaining -= cutoff
        i += 1

    # assert that all portions have been distributed
    # assert(sum(distribution) == num_portions)
    # print(distribution)
    return distribution
