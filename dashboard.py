import base64
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, html, dash_table, dcc, callback, Output, Input
from io import BytesIO


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


with open('counties.json') as f:
    counties = json.load(f)
f.close()
data = [{'county': x['name'], 'state': x['state'], 'year': k} | v for x in counties if 'elections' in x for k, v in x['elections'].items()]
data = [x | {'dem_share': x['dem'] / x['total']} | {'gop_share': x['gop'] / x['total']} for x in data]
dem2008 = [x['dem'] / x['total'] for x in data if x['year'] == '2008']
gop2008 = [x['gop'] / x['total'] for x in data if x['year'] == '2008']
dem2016 = [x['dem'] / x['total'] for x in data if x['year'] == '2016']
gop2016 = [x['gop'] / x['total'] for x in data if x['year'] == '2016']

# fig, ax = plt.subplots()
# ax.hist(dem2008, color='blue', label='Dem 2008')
# ax.hist(gop2008, color='red', label='GOP 2008')
# ax.hist(dem2016, color='blue', label='Dem 2016')
# ax.hist(gop2016, color='red', label='GOP 2016')
# ax.set_xlabel('Vote share')
# ax.set_ylabel('Frequency')
# ax.legend()
# fig.tight_layout()
# fig_to_uri(fig)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div(className='row', children='USA Presidential election data',
             style={'textalign': 'left', 'fontSize': 30}
    ),
    
    html.Div(className='row', children=[
        dcc.RadioItems(options=['2008', '2016', 'both'], value='both', inline=True, id='year-buttons')
    ]),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dash_table.DataTable(data=data, page_size=20),
        ]),
        html.Div(className='six columns', children=[
            dcc.Graph(figure={}, id='vote-share-chart')
        ])
    ])
])

@callback(
    Output(component_id='vote-share-chart', component_property='figure'),
    Input(component_id='year-buttons', component_property='value')
)
def update_graph(year):
    fig = go.Figure()
    if year == '2008':
        fig.add_trace(go.Histogram(x=dem2008, name='Obama, 2008'))
        fig.add_trace(go.Histogram(x=gop2008, name='McCain, 2008'))
    elif year == '2016':
        fig.add_trace(go.Histogram(x=dem2016, name='Clinton, 2016'))
        fig.add_trace(go.Histogram(x=gop2016, name='Trump, 2016'))
    else:
        fig.add_trace(go.Histogram(x=dem2008, name='Obama, 2008'))
        fig.add_trace(go.Histogram(x=gop2008, name='McCain, 2008'))
        fig.add_trace(go.Histogram(x=dem2016, name='Clinton, 2016'))
        fig.add_trace(go.Histogram(x=gop2016, name='Trump, 2016'))
    fig.update_layout(
        xaxis_title_text='Share of vote by party in county',
        yaxis_title_text='Frequency',
        barmode='overlay')
    fig.update_traces(opacity=0.6)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)