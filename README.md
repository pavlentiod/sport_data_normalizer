# README SFR

## Overview
This Python code is designed to extract and process sport orienteering event results from a given link. The code utilizes web scraping techniques to extract relevant information from the event's web page, such as split times, routes, and log details. The extracted data is then organized into a Pandas DataFrame for further analysis.

## Dependencies
Make sure you have the following Python libraries installed before running the code:
- `random`
- `typing`
- `pandas`
- `requests`
- `beautifulsoup4`

You can install them using the following command:
```bash
pip install pandas requests beautifulsoup4
```

## How to Use
1. Import the necessary libraries in your Python script or Jupyter notebook.
```python
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
```

2. Copy and paste the entire code into your project.

3. Use the `SFR_EVENT` function to extract and process the orienteering event results.
```python
link = "https://example.com/orienteering-event"
df, routes, log = SFR_EVENT(link)
```

4. The function returns three components:
   - `df`: A Pandas DataFrame containing split times, routes, and log details for each participant.
   - `routes`: A dictionary containing dispersion details for each group.
   - `log`: A log message indicating the status of the extraction process.

#README for split.py
# SFR Event Data Analysis

This Python repository offers tools for analyzing data from SFR (Sport Federation of Rogaining) events, specifically focusing on split times and results of participants in rogaining competitions.

## General Description

Rogaining is a sport that involves long-distance cross-country navigation, combining elements of orienteering and endurance. The provided code helps analyze participant performance in SFR rogaining events, offering insights into split times, group comparisons, and overall results.

## Prerequisites

Before using the code, ensure you have the necessary dependencies installed:

- **pandas**: A powerful data manipulation library.
- **openpyxl**: A library for reading and writing Excel files.

You can install these dependencies using the following command:

```bash
pip install pandas openpyxl
```

## Usage Instructions

1. Import the required libraries:

```python
import pandas as pd
from pandas.core.frame import DataFrame
from pandas.core.series import Series
from spl_machine.SFR import SFR_EVENT
from names_and_sex_js import all_names
import datetime
import openpyxl
import re
```

2. Set a placeholder for null values:

```python
# Placeholder for null values in timedelta calculations
null = pd.Timedelta(seconds=0)
```

3. Define a list to store names not found in the provided names list:

```python
# List to store names not found in the provided names list
not_found = []
```

4. Utilize the provided functions for sorting names based on gender, finding gender of a given name, filtering the DataFrame based on group or gender, and formatting timedelta values as strings.

5. Use functions for finding data based on filter criteria, formatting names in a specific way, checking control points for a given distance, creating a DataFrame for an event, and getting the distance for a given name and group.

6. Leverage functions for creating lists of splits and general times for a given name and data, finding indexes of null values and delimiter for general times, and creating a DataFrame with split data for a given name and group.

7. Employ the provided function for calculating the stability grade based on given values.

8. Utilize functions for obtaining general route information for a given name, group, backlog, and distance.

9. Calculate self-backlog for a given split time, backlog, and median using the provided function.

10. Extract results for a given data, group, and routes using the provided function.

11. Use the function to find names with the same routes.

12. A placeholder function for grading is provided, which can be extended based on specific requirements.

13. Example usage:

```python
# Example usage
df, routes, log = SFR_EVENT('https://o-site.spb.ru/_races/231015_LO/split2.htm')
name = 'ИВАНОВ ПАВЕЛ'
split_file = f'lo_midl_{name.split(" ")[0]}_{name.split(" ")[1][:1]}.xlsx'
SPL(df, routes, name, "М21")
```
