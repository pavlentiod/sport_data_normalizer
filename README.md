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

