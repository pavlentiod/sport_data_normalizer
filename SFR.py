# Import necessary libraries
import random
from typing import Union
import pandas as pd
from pandas import Timedelta
import requests
from bs4 import BeautifulSoup as BS
from bs4.element import ResultSet
import re
import chardet
from pandas._libs import NaTType

# Global variable for logging
global log

""" COMMON PART """

""" AUXILIARY FUNCTIONS"""

# Function to create a BeautifulSoup object from a string
def bs(s: BS):
    soup: BS = BS(str(s), 'html.parser')
    return soup

# Function to format a list of course data
def course(l: list):
    r = range(len(l) - 1)
    f = lambda x: re.sub(r', ', '->', str(x))[1:-1]
    return [f(l[i:i + 2]) for i in r]

# Placeholder for null values in the time calculations
null: Union[Timedelta, NaTType, NaTType] = Timedelta(seconds=0)

# Function to convert a list of points to routes
def points_to_routes(l: list):
    f = lambda x, i: f'{x[i]}->{x[i + 1]}'
    l: list = [f(l, i) for i in range(len(l) - 1)]
    return l

# Function to create a range for iteration
def rl(l: list):
    return range(len(l))

""" ......  """

# Function to create a BeautifulSoup object from a text file
def soup_from_txt(n):
    with open(f'pages\page{n}.txt', 'r') as f:
        return bs(f.read())

"""////"""

# Function to parse a web page and return the BeautifulSoup object
def web_parse(link: str):
    response = requests.get(link)
    try:
        content = response.content.decode(response.encoding)
    except UnicodeDecodeError:
        content = ''
    soup_page = bs(content)
    return soup_page

# Function to extract main information from the BeautifulSoup object
def soup_main_info(soup: BS):
    h2: list = [i.get_text(' ').upper() for i in soup.find_all('h2')]
    tables: ResultSet = soup.find_all('table')
    return h2, tables

# Function to check the number of people in each group
def check_void_groups(soup: BS):
    h2, tables = soup_main_info(soup)
    number_of_sportsmens: dict = {h2[i]: len(bs(tables[i]).find_all('tr')) - 1 for i in rl(h2)}
    return number_of_sportsmens

""" WORK WITH ONE GROUP """

# Function to extract data for a specific group from the BeautifulSoup object
def BS_group_data(group: str, soup: BS):
    h2, tables = soup_main_info(soup)
    group_soup: BS = bs(tables[h2.index(group)])
    tr = group_soup.find_all('tr')
    th = group_soup.find_all('th')
    return group_soup, tr, th

# Function to extract group names
def group_names(group: str, tr: ResultSet):
    tr_pt: BS = bs(tr[1])
    td_pr: ResultSet = tr_pt.find_all('td', class_='cr')
    all_td: ResultSet = bs(''.join(str(tr))).find_all('td', class_='cr')
    td: list = [all_td[i].get_text(' ') if all_td[i].get_text("") != '' else f"ND{i}" for i in rl(all_td)]
    if " " in td_pr[0].get_text(' ') or "\n" in td_pr[0].get_text(' '):
        names: list = [i.upper() + f"^{group.upper()}" for i in td[::len(td_pr)]]
    elif len(td_pr) == 3:
        d_ind: list = [j * 3 - 1 for j in range(1, len(td))]
        names: list = [td[i] for i in rl(td) if i not in d_ind]
        names: list = [" ".join(
            names[i:i + 2]).upper() + f"^{group.upper()}" \
                       for i in rl(names)][:-1:2]
    elif len(td_pr) == 4:
        names: list = [td[i].upper() + ' ' + td[i + 1].upper() + f"^{group.upper()}" for
                       i in range(len(td) - 1)][::2][::2]
    elif len(td_pr) == 2 and " " not in td_pr[0].get_text(' ') or "\n" in td_pr[0].get_text(' '):
        names: list = [i.upper() + f"^{group.upper()}" for i in
                       td[::len(td_pr)]]
    else:
        raise ValueError('Names not found')
    names = [re.sub(' +', ' ', i) for i in names]
    names = [i if names.count(i) == 1 else f'{i.split("^")[0]}*{random.randint(0, 100)}^{group.upper()}' for i in names]
    return names

""" Check protocols for the presence of control points """

# Function to extract results for a group
def group_results(tr: ResultSet, names: list):
    f = lambda x: re.search('\d+:\d+:\d+', x)
    s = [f(str(i)).group() if f(str(i)) is not None else '00:00:00' for i in tr[1:]]
    all_res = [Timedelta(hours=int(i.split(':')[0]), minutes=int(i.split(':')[1]),
                         seconds=int(i.split(':')[2])) if ':' in i else null for i in s]
    return dict(zip(names, all_res))

# Function to extract points and create a dictionary with routes for each person
def points(tr: ResultSet, th: ResultSet, tm_index: int,
           names: list):
    r = rl(tr)[:-1]
    if len(th[tm_index].get_text(' ')) > 3:
        cp = lambda s: int(re.search('\(\d{1,3}\)', s).group()[1:-1])
        disp: list = [241] + [cp(i.text) for i in th[tm_index:]]
        return dict(zip(names, [course(disp) for i in r]))
    f = lambda x: re.search('\[\d{2,3}\]', str(x))
    l: list = []
    for j in r:
        s = bs(tr[j + 1]).find_all('td')
        dist = [241] + [int(f(i).group()[1:-1]) if f(i) is not None else 00 for i in s[tm_index:-1]] + [240]
        l.append(course(dist))
    return dict(zip(names, l))

# Function to calculate dispersions
def dispersions(d: dict):
    disp = {}
    groups = {}
    for key, value in d.items():
        if value not in disp.values():
            disp[f"disp{len(disp) + 1}"] = value
        groups.setdefault(f"group{list(disp.values()).index(value) + 1}", []).append(key)
    keys = [str(i) for i in disp.values()]
    final_dict = dict(zip(keys, groups.values()))
    return final_dict

""" WORK WITH INDIVIDUAL """

# Function to extract times for each participant
def times(tr: ResultSet, tm_index: int):
    times = []
    for i in rl(tr):
        td: ResultSet = bs(tr[i]).find_all('td')
        f = lambda x: re.search('\d+:\d{2,3}', x).group()
        t: list = [f(i.get_text(' ')) if i.text != '' else '00:00' for i in td[tm_index:]]
        t_delta: list = [null] + [Timedelta(minutes=int(i.split(':')[0]), seconds=int(i.split(':')[1])) for i in t]
        times.append(t_delta)
    return times

# Function to calculate splits
def splits(times: list, names: list):
    spl = []
    for l in times:
        f = lambda x, i: x[i] - x[i - 1] if x[i] > x[i - 1] else null
        t: list = [f(l, i) for i in range(1, len(l))]
        spl.append(t)
    ret = dict(zip(names, spl))
    return ret

# Function to create a dictionary with routes and splits
def routes_and_splits_dict(routes: list, splits: list):
    if len(routes) == len(splits):
        d: dict = dict(zip(routes, splits))
        return d
    else:
        raise ValueError(f'{len(routes), len(splits)} lengths are not the same')

""" GROUP PROCESSING """

# Function to create a DataFrame for a group and calculate dispersions
def group_frame(group: str, soup: BS):
    stages = [group]
    # Extract data, check for tm_index
    group_soup, tr, th = BS_group_data(group.upper(), soup)
    stages.append('group_frame 1')
    tm_index = [th.index(i) for i in th if "#" in i.get_text()]
    stages.append('group_frame 2')
    names = group_names(group.upper(), tr)
    stages.append('group_frame 3')
    results = group_results(tr, names)
    stages.append('group_frame 4')
    try:
        tm_index = tm_index[0]
        stages.append('group_frame 5')
    except IndexError:
        disps = {'RES': names}
        stages.append('group_frame 5 error')
        return pd.DataFrame(results, index=['RES']).T, disps
    try:
        points_l = points(tr, th, tm_index, names)
        stages.append('group_frame 6')
        times_l = times(tr[1:], tm_index)
        stages.append('group_frame 7')
    except AttributeError:
        stages.append('group_frame 7 error')
        return pd.DataFrame(results, index=['RES']).T
    splits_l = splits(times_l, names)
    stages.append('group_frame 8')
    # Process times and create a dictionary for each person
    GD = {}
    for name in names:
        try:
            sportsmen_info = routes_and_splits_dict(points_l[name], splits_l[name])
        except ValueError:
            sportsmen_info = {}
        sportsmen_info.setdefault('RES', results[name])
        GD.setdefault(name, sportsmen_info)
    disps = dispersions(points_l)
    stages.append('group_frame 11')
    df = pd.DataFrame(GD).T
    stages.append('group_frame 12')
    return df, disps

# Function to process an entire event
def SFR_EVENT(link: str):
    stages = []
    stages.append('stage1')
    sp = web_parse(link)
    stages.append('stage2')
    h2, tb = soup_main_info(sp)
    stages.append('stage3')
    global log
    try:
        check = check_void_groups(sp)
    except IndexError:
        log = 'index error'
        return pd.DataFrame(), {}, log
    stages.append('stage4')
    groups = [i.upper() for i in h2 if check[i] != 0]
    df = pd.DataFrame()
    routes = {}
    for group in groups:
        stages = ['stage1', 'stage2', 'stage3', 'stage4']
        try:
            group_df, disps = group_frame(group, sp)
        except:
            group_df = pd.DataFrame()
            disps = {}
            log = 'group frame error'
            return pd.DataFrame(), {}, log
        df = pd.concat([df, group_df], join='outer', axis=0)
        stages.append('stage7')
        routes.setdefault(group, disps)
        stages.append('stage8')
    log = 'correct'
    df = df.replace([null], pd.NaT)
    df = df.dropna(axis=1, how='all')
    return df, routes, log
