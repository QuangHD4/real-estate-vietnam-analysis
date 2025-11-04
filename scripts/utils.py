import re
from typing import Literal, Tuple, Optional, List, Dict
import pandas as pd
from tqdm import tqdm

def extract_numeric(s:str):
    num_str = re.search(r"^(\d+.?\d*,?\d*)\D?", s).group(1)
    num_str = num_str.replace('.','')
    num_str = num_str.replace(',','.')
    return float(num_str)

def extract_coordinates(embed_map_link:str) -> Tuple[str, str]:
    latitude, longitude = re.search(r"q=(\d+\.?\d*),(\d+\.?\d*)\D?", embed_map_link).groups()
    return float(latitude), float(longitude)
