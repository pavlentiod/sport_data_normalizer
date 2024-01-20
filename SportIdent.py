from bs4 import BeautifulSoup as BS
import pandas as pd
from pandas import Timedelta
import requests
import numpy as np
import re
import datetime
import random

# Placeholder for null values in timedelta calculations
null = Timedelta(seconds=0)

# Function to remove duplicate elements from a list
def rem_doubles(l):
    rd = []
    [rd.append(i) for i in l if i not in rd]
    return rd

# Function to parse and clean the split time or control point number from a string
def clear(s, par):
    if par == 1:
        if s[:6] == ' ' * 6:
            n_strip = [i for i in re.split('( )', s.strip()) if ":" in i]
            try:
                spl = [Timedelta(hours=int(i.split(':')[0][:]), minutes=int(i.split(':')[1][:]),
                                 seconds=int(i.split(':')[2][:2])) for i in n_strip]
                return spl
            except ValueError:
                spl = [Timedelta(minutes=int(i.split(':')[0][:]),
                                 seconds=int(i.split(':')[1][:2]))
                       for i in n_strip]
                return spl
        else:
            return [Timedelta(minutes=1)]
    elif par == 2:
        s2 = ['Start'] + [i[:-1] for i in re.split("( )", s.strip()) if
                          i.isspace() is False and i != '' and i[-1] == ')']
        return s2
    elif par == 3:
        try:
            pass
        except ValueError:
            return s

# Function to extract participant names from a BeautifulSoup group tag
def names(gr):
    lines = gr.get_text(' ').splitlines()
    lines = [i for i in lines if i[:len(big_space)] != big_space][2:]
    n_list = [i[5:i.index('    ')] for i in lines]
    return n_list

# Function to extract header points from a BeautifulSoup group tag
def head_points(b):
    b = b.get_text(' ')
    tm_index = [b.split('     ').index(i) for i in [i if i != '' else ' ' for i in b.split('     ')] if
                i[0].strip().isdigit()][0]
    st = b.split('     ')[tm_index:]
    n = ['Start'] + [i.strip()[-3:-1] for i in st]
    disp = [str(n[i:i + 2]) for i in range(len(n) - 1)]
    disp = [i.split(',')[0][2:-1] + '->' + i.split(',')[1][2:-2] for i in disp]
    return [disp]

# Function to extract dispersions from a BeautifulSoup group tag
def dispersions(group):
    lines = group.get_text(' ').splitlines()[2:]
    spl_lines = [lines[lines.index(i)] for j in names(group) for i in lines if j in i]
    dispersions = [
        [str(clear(i.split('     ')[-1], 2)[j:j + 2]) for j in range(len(clear(i.split('     ')[-1], 2)) - 1)] for i in
        spl_lines]
    dispersions = [i.split(',')[0][2:-1] + '->' + i.split(',')[1][2:-2] if i != [] else 'Start->90' for i in
                   dispersions]
    return dispersions

# Function to calculate time differences between control points
def dist(l):
    l_range = range(len(l) + 1)
    l = [null] + l
    new = [l[i] - l[i - 1] if l[i] <= l[-1] else null for i in l_range][1:]
    return new

# Function to extract names and results from a given link
def names_and_res(link):
    response = requests.get(link)
    content = response.content.decode(response.encoding)
    bs = BS(content, 'html.parser')
    pre = bs.find_all('pre')[:-1]
    all_names = {}
    all_res = {}
    all_fin = {}
    for i in pre:
        group_res = []
        gr_name = bs.find_all('h2')[pre.index(i)].get_text(' ')
        lines = i.get_text(' ').splitlines()
        lines = [i for i in lines if i[:len(big_space)] != big_space][2:]
        for line in lines:
            line = line[40:80]
            t = Timedelta(seconds=0)
            for line_n in range(len(lines)):
                try:
                    d = datetime.datetime.strptime(line.strip()[line_n:line_n + 8], "%H:%M:%S")
                    t = Timedelta(hours=d.hour, minutes=d.minute, seconds=d.second)
                except:
                    continue
            group_res.append(t)
        n_list = [i[5:i.index('    ')] + "_" + gr_name.split(' ')[0] for i in lines]
        n_list = [i if n_list.count(i) == 1 else i + f'_{random.randrange(1, 1000)}' for i in n_list]
        fin_l = [Timedelta(minutes=int(i.split(' ')[-1].split(':')[0]), seconds=int(i.split(' ')[-1].split(':')[1])) if i.split(' ')[-1].strip() != '' else Timedelta(hours=1) for
                 i in lines]
        print(len(n_list), len(fin_l))
        all_names.setdefault(gr_name.split(' ')[0], n_list)
        all_res.setdefault(gr_name.split(' ')[0], group_res)
        all_fin.setdefault(gr_name.split(' ')[0], fin_l)
    return all_names, all_res, all_fin

# Function to create a DataFrame for split times and results
def frame_SI(link):
    response = requests.get(link)
    try:
        content = response.content.decode(response.encoding)
    except UnicodeDecodeError:
        content = ''
    soup_page = BS(content, 'html.parser')
    pre = soup_page.find_all('pre')[:-1]
    all_names, all_res, all_fin = names_and_res(link)
    distanses = {}
    df = pd.DataFrame()
    for group in pre[:]:
        gr_dict = {}
        gr_name = list(all_names.keys())[pre.index(group)]
        names_l = all_names[gr_name]
        res_l = all_res[gr_name]
        fin_l = all_fin[gr_name]
        lines = group.get_text(' ').splitlines()[2:]
        u_lines = [lines[lines.index(i) + 1] for j in names_l for i in lines if
                   j.split('_')[0] in i and len(lines) - lines.index(i) > 1]
        if len(u_lines) < len(names_l):
            u_lines = u_lines + [' '] * (len(names_l) - len(u_lines))
        if '(' not in u_lines[0]:
            dispers = dispersions(group)
        else:
            dispers = head_points(BS(str(group), "html.parser").find('b'))
        times = [dist(clear(i, 1)) for i in u_lines]
        n_range = range(len(names_l))
        distanses.setdefault(gr_name, dispers[0] + ['FINISH'])
        for name_n in n_range:
            if len(dispers) != 1:
                points = dispers[name_n]
                splits = times[name_n]
                r_points = range(len(points))
                s_dict = {points[i]: splits[i] for i in r_points if
                          points[i].split('->')[0] != points[i].split('->')[1]}
            else:
                points = dispers[0]
                splits = times[name_n]
                r_points = range(len(points))
                if len(points) != len(splits):
                    splits = splits + [Timedelta(seconds=0)] * (len(points) - len(splits))
                s_dict = {points[i]: splits[i] for i in r_points if
                          points[i].split('->')[0] != points[i].split('->')[1] and len(splits) > 1}
            s_dict.setdefault('RES', res_l[name_n])
            s_dict.setdefault('FINISH', fin_l[name_n])
            gr_dict.setdefault(names_l[name_n], s_dict)
        df = pd.concat([df, pd.DataFrame(gr_dict).T], join='outer', axis=0)
    df.replace([pd.Timedelta(seconds=0)], pd.NA, inplace=True)
    df.dropna(how='all', axis=1)
    df.index.name = soup_page.find('h1').get_text(' ')[:100]
    print(distanses)
    return df

# Example usage of the frame_SI function
d4 = 'http://vlacem.ru/Arhiv/2023/ChR2023_Vyazniki/Res/1%20-%20Split%20_%2019052023.htm'
frame_SI(d4).to_csv('chemp19.05.csv')
users = open('users.txt', 'r').read().splitlines()
users = [i for i in users if i != '@pavlenti0d']
print(len(users))
