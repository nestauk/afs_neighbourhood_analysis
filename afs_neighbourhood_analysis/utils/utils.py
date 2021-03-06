import os
from pathlib import Path
from PIL import ImageColor
from matplotlib.colors import LinearSegmentedColormap
import json
from afs_neighbourhood_analysis import PROJECT_DIR
import pandas as pd


def load_colours():
    with open(f"{PROJECT_DIR}/inputs/data/aux/colours.json", "r") as colour_file:
        data = colour_file.read()
    colours = json.loads(data)
    return colours


def nestafont():
    font = "Averta"

    return {
        "config": {
            "title": {"font": font},
            "axis": {"labelFont": font, "titleFont": font},
            "header": {"labelFont": font, "titleFont": font},
            "legend": {"labelFont": font, "titleFont": font},
        }
    }


def hex_to_cm(array, **kwargs):
    rgb = [(ImageColor.getcolor(i, "RGB")) for i in array if i != "#FFFFFF"]
    rgb_plt = [tuple([i / 255 for i in val]) for val in rgb]
    n_bin = len(rgb_plt)
    cmap = kwargs.get("cmap_name", "my_cmap")
    return LinearSegmentedColormap.from_list(cmap, rgb_plt, N=n_bin)


def clean_table_names(table: pd.DataFrame, columns: list, clean_dict: dict):
    """This function cleans table names before visualising them
    Args:
        table: table we want to clean
        columns: list of columns to clean
        clean_dict: dictionary mapping raw variable values and clean values
    """

    table_ = table.copy()
    for c in columns:
        table_[c] = table_[c].map(clean_dict)
    return table_
