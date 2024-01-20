import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from spl_machine.SFR import SFR_EVENT
from names_and_sex_js import all_names
import datetime
import openpyxl
import re

# Placeholder for null values in timedelta calculations
null = pd.Timedelta(seconds=0)

# List to store names not found in the provided names list
not_found = []

# Function to sort names based on gender
def sort2(names, all_names):
    male_names = []
    female_names = []
    undefined_names = []
    for name in names:
        split_names = re.split('[ ^]', name.upper())
        first_name = [i for i in split_names if i in all_names]
        if len(first_name) != 0:
            if all_names[first_name[0]] == 'Ж':
                female_names.append(name)
            elif all_names[first_name[0]] == 'М':
                male_names.append(name)
        else:
            undefined_names.append(name)
    return male_names, female_names, undefined_names

# Function to sort names by gender
def sortsex(names):
    sorted_names = sort2(names, all_names)
    names_dict = {key: val for key, val in zip(['M', 'F', 'Undefined'], sorted_names) if val != []}
    return names_dict

# Function to find the gender of a given name
def find_sex(name):
    sorted_names = sortsex([name])
    sex = [i for i in sorted_names if sorted_names[i] != []][0]
    return sex

# Function to filter the DataFrame based on group or gender
def filter_df(df: DataFrame, routes, group='', sex=''):
    if group != '':
        group_indexes = [i for v in routes[group].values() for i in v]
        df_filter: DataFrame = df.loc[group_indexes].dropna(how='all', axis=1)
    elif sex != '':
        indexes = sortsex(df.index)[sex]
        df_filter: DataFrame = df.loc[indexes]
    else:
        df_filter = df
    return df_filter

# Function to format timedelta values as strings
def format(t: pd.Timedelta):
    if t in [pd.NaT, '']:
        return '-'
    if t < null:
        t = abs(null - t)
        sign = '-'
    else:
        sign = ' '
    t = re.search('\d+:\d+:\d+', str(t))
    dt = datetime.datetime.strptime(t.group(), '%H:%M:%S')
    if dt.hour == 0:
        return sign + dt.strftime('%M:%S')
    else:
        return sign + dt.strftime('%H:%M:%S')

# Function to find data based on filter criteria
def find_data(df, filt, name, group, routes):
    if filt == 'group':
        data = filter_df(df, routes=routes, group=group.upper())
    elif filt == 'sex':
        sex = find_sex(name)
        if sex != 'Undefined':
            data = filter_df(df, sex=sex, routes=routes)
        else:
            data = filter_df(df, routes=routes)
    else:
        data = filter_df(df, routes=routes)
    return data

# Function to format the name in a specific way
def name_format(s):
    s1 = s.split('^')
    s2 = s1[0]
    s3 = f'{s2[:(s2 + " ").index(" ") + 2]}.[{s1[-1]}]'
    return s3

# Function to check control points for a given distance
def check_cp(dist: list, data: DataFrame, name: str):
    if '-' in dist:
        return dist
    else:
        s: Series = data.loc[name]
        not_null = [i for i in s.dropna(axis=0).index]
        d = [i if i in not_null else '-' for i in dist]
        return d

# Function to create a DataFrame for an event
def event_frame(file: str):
    df: DataFrame = pd.read_csv(file, index_col=0, encoding='utf-8').apply(pd.to_timedelta)
    df.replace([pd.Timedelta(seconds=0)], pd.NA, inplace=True)
    df.dropna(how='all', axis=1)
    return df

# Function to get the distance for a given name and group
def distance(routes: dict, name: str, group: str):
    d = routes[group]
    try:
        dist = eval([i for i in d if f'{name}^{group}' in d[i]][0])
    except:
        dist = [i for i in d if f'{name}^{group}' in d[i]][0]
    dist = [i if '0' not in str(i).split('->') else '-' for i in dist]
    return dist

# Function to create a list of splits for a given name and data
def splits_list(name_data, dist, R):
    split_time = [name_data[dist[i]] if i != '-' else '-' for i in R]
    return split_time

# Function to create a list of general times for a given name and data
def general_times_list(name_data, dist, nn, delim):
    part1 = dist[:nn[0]]
    part2 = dist[nn[-1] + 1:]
    try:
        general_time = [name_data[part1[:i]].sum() for i in range(1, len(part1) + 1)] + delim + [
            name_data['RES'] - name_data[part2[i:]].sum() for i in range(1, len(part2) + 1)]
    except:
        general_time = [''] * len(dist)
    return general_time

# Function to find the indexes of null values and delimiter for general times
def find_nn(dist):
    if '-' in dist:
        nn = [n for n, i in enumerate(dist) if i == '-']
        delim = ['-'] * (nn[-1] - nn[0] + 1)
    else:
        nn = [len(dist)]
        delim = []
    return nn, delim

# Function to create a DataFrame with split data for a given name and group
def split_table_data(dist: list, data: DataFrame, name: str, group: str):
    name = f'{name.upper()}^{group.upper()}'
    dist = check_cp(dist, data, name)
    nn, delim = find_nn(dist)
    nn = sorted(nn)
    name_data = data.loc[name]
    if list(name_data.dropna().index) == ['RES']:
        mode = 0
        col = ['n', 'gt', 's', 'bk', 'p_bk', 'l', 's_p']
        return pd.DataFrame(columns=col), mode
    else:
        mode = 1
    try:
        R = [r if r not in range(nn[0], nn[-1] + 1) else '-' for r in range(len(dist))]
        num = find_num(dist, nn, R)
        split_time = splits_list(name_data, dist, R)
        general_times = general_times_list(name_data, dist, nn, delim)
        backlog, percent_bk = split_backlog(name_data, data, dist, R)
        spl_leader = split_leaders(data, dist, R)
        split_places = split_place(name_data, data, dist, R)
        col = ['n', 'gt', 's', 'bk', 'p_bk', 'l', 's_p']
        val = [num, general_times, split_time, backlog, percent_bk, spl_leader, split_places]
        SPL = {k: v for k, v in zip(col, val)}
        df = pd.DataFrame(SPL).set_index(['n'])
        return df, mode
    except:
        print('error with split data', name)
        mode = 0
        col = ['n', 'gt', 's', 'bk', 'p_bk', 'l', 's_p']
        return pd.DataFrame(columns=col), mode

# Function to calculate the stability grade based on the given values
def calculate_stability_grade(values):
    values.replace(['-'], pd.NA, inplace=True)
    standard_deviation = values.std()
    stability = round(100 - standard_deviation) if 100 > standard_deviation else 20
    return stability

# Function to get general route information for a given name, group, backlog, and distance
def general_route_info(name, group, p_backlog, dist, data):
    name = f'{name.upper()}^{group.upper()}'
    p_backlog.replace(['-'], pd.NA, inplace=True)
    res = data.loc[name]['RES'] if 'RES' in data.loc[name].index else null
    median = round(p_backlog.median(), 2)
    best_times = [pd.Timedelta(data[i].sort_values().values[0]) for i in dist]
    best_lead_res = pd.Series(best_times).sum()
    best_lead_bk = res - best_lead_res
    stab = calculate_stability_grade(p_backlog)
    return stab, median, res, best_lead_res, best_lead_bk

# Function to calculate self-backlog for a given split time, backlog, and median
def self_bk(split_time, backlog, median):
    backlog1 = [i if i != '-' else pd.Timedelta(-1) for i in backlog]
    backlog2 = [i if i > null else null for i in backlog1]
    RVP = [i - ((i - j) * (1 + median / 100)) if i != '-' else '-' for i, j in zip(split_time, backlog2)]
    RVP_sum = pd.DataFrame([i for i in RVP if i != '-']).sum()
    return RVP, RVP_sum

# Function to get results for a given data, group, and routes
def results(data, group, routes):
    names = [i for v in routes[group].values() for i in v]
    df = pd.DataFrame(index=names)
    df.index.name = 'name'
    res_frame = data.loc[names]['RES']
    leader_res = res_frame[0]
    res = list(res_frame.values)
    backlogs = list(res_frame.apply(lambda x: x - leader_res if x != pd.NaT else pd.NaT))
    df['res'] = res
    df['l_bk'] = backlogs
    group_routes = list(routes[group])
    same_route_sportsmens = find_same_routes(group_routes, routes)
    general_res_frame = pd.DataFrame(data.loc[same_route_sportsmens]['RES'].sort_values())
    leader_res2 = general_res_frame['RES'].values[0]
    general_res_frame['l_bk'] = list(
        general_res_frame['RES'].apply(lambda x: x - leader_res2 if x != pd.NaT else pd.NaT))
    return df, general_res_frame

# Function to find names with the same routes
def find_same_routes(group_routes, routes):
    groups = [gr for gr in routes for r in routes[gr] if r in group_routes]
    names = []
    for group in groups:
        names += [i for v in routes[group].values() for i in v]
    return list(set(names))

# Placeholder function for grading
def grade():
    pass

# Example usage
df, routes, log = SFR_EVENT('https://o-site.spb.ru/_races/231015_LO/split2.htm')
name = 'ИВАНОВ ПАВЕЛ'
split_file = f'lo_midl_{name.split(" ")[0]}_{name.split(" ")[1][:1]}.xlsx'
SPL(df, routes, name, "М21")
