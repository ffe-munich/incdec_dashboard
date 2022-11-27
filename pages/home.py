
import os
import nashpy as nash
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from utils.layout import layout_func_home as layout_func
import dash
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, Input, Output, callback

dash.register_page(__name__, path='/')

layout = layout_func()