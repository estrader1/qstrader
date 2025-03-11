BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = range(8)


def string_colour(text, colour=WHITE):
    """
    Create string text in a particular colour to the terminal.
    """
    seq = "\x1b[1;%dm" % (30 + colour) + text + "\x1b[0m"
    return seq

import json
from pandas import Timestamp
import pandas as pd


def convert_timestamps_nans(obj):
    if isinstance(obj, dict):
        return {k: convert_timestamps_nans(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps_nans(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_timestamps_nans(item) for item in obj)  # Convert tuple elements
    elif isinstance(obj, Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):  # Check for NaN values
        return 0
    return obj
