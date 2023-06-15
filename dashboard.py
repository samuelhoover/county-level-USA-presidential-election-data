import base64
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, html, dash_table, dcc, callback, Output, Input
from io import BytesIO


# if using Matplotlib for creating figures
def fig_to_uri(in_fig, close_all=True, **save_args):
    """
    # type: (plt.Figure) -> str
    Save a figure as a URI
    :param in_fig:
    :return:
    """
    out_img = BytesIO()
    in_fig.savefig(out_img, format='png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return f'data:image/png;base64,{encoded}'


# read in JSON file
with open('counties.json') as f:
    counties = json.load(f)
f.close()

# sort county and state names alphabetically
counties = sorted(sorted(counties, key=lambda x: x['name']), key=lambda x: x['state'])

# create subset of US presidential election data
data = [{'county': x['name'], 'state': x['state'], 'year': k} | v for x in counties if 'elections' in x for k, v in x['elections'].items()]
# calculate vote share by party in each county for each presidential election and save as key-value pairs
data = [x 
        | {'dem_share': np.round(x['dem'] / x['total'], 3)} 
        | {'gop_share': np.round(x['gop'] / x['total'], 3)} 
        | {'other_share': np.round((x['total'] - x['dem'] - x['gop']) / x['total'], 3)} for x in data]

# import CSS style sheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

# dashboard
app.layout = html.Div([
    html.Div(className='row', children='USA Presidential election data',
             style={'textalign': 'left', 'fontSize': 30}
    ),
    
    html.Div(className='row', children=[
        dcc.Dropdown(
            id='year-dropdown', 
            options=['2008', '2012', '2016', '2020'], 
            multi=True, 
            placeholder='Select year(s)', 
            clearable=True
        )
    ]),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dash_table.DataTable(data=data, page_size=30),
        ]),
        html.Div(className='six columns', children=[
            dcc.Graph(id='vote-share-chart', figure={})
        ])
    ])
])

@callback(
    Output(component_id='vote-share-chart', component_property='figure'),
    Input(component_id='year-dropdown', component_property='value')
)
def update_graph(year):
    fig = go.Figure()
    fig.update_layout(
        xaxis_range=[0, 1],
        xaxis_title_text='Share of vote by party in county',
        yaxis_title_text='Frequency',
        barmode='overlay'
    )
    if year is None:
        return fig
    else:
        for y in year:
            fig.add_trace(go.Histogram(
                x=[x['dem_share'] for x in data if x['year'] == y], name=f'Dem, {y}'
            ))
            fig.add_trace(go.Histogram(
                x=[x['gop_share'] for x in data if x['year'] == y], name=f'GOP, {y}'
            ))
    fig.update_traces(opacity=0.6)
    return fig

# TODO:
# add map for county vote share

if __name__ == '__main__':
    app.run_server(debug=True)