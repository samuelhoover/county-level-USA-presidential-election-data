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


# -----------------------------------------------------------------------------
# import and clean data
# read in CSV file into DataFrame
df = pd.read_csv(
    'https://raw.githubusercontent.com/evangambit/JsonOfCounties/master/counties.csv'
)
election_cols = ['name', 'state'] + [x for x in df.columns if x.startswith('election')]
election_df = df[election_cols].fillna(0)  # fill NaN with 0

# read in JSON file into dictionary
with open('counties.json') as f:
    counties = json.load(f)
f.close()

# sort county and state names alphabetically
counties = sorted(sorted(counties, key=lambda x: x['name']), key=lambda x: x['state'])

# create subset of US presidential election data
election_data = [{'county': x['name'], 'state': x['state'], 'year': k} | v for x in counties if 'elections' in x for k, v in x['elections'].items()]
# calculate vote share by party in each county for each presidential election and save as key-value pairs
election_data = [x 
        | {'dem_share': np.round(x['dem'] / x['total'], 3)} 
        | {'gop_share': np.round(x['gop'] / x['total'], 3)} 
        | {'other_share': np.round((x['total'] - x['dem'] - x['gop']) / x['total'], 3)} for x in election_data]
# calculate nationwide popular vote for 
pop_vote_data = {
    'dem': [sum([x['dem'] for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']],
    'gop': [sum([x['gop'] for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']],
    'other': [sum([(x['total'] - x['dem'] - x['gop']) for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']]
}

# -----------------------------------------------------------------------------
# Nationwide popular vote figure
pop_vote_fig = go.Figure()
pop_vote_fig.add_scatter(
    x=['2008', '2012', '2016', '2020'],
    y=[sum([x['dem'] for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']],
    mode='lines',
    name='Dem'
)
pop_vote_fig.add_scatter(
    x=['2008', '2012', '2016', '2020'],
    y=[sum([x['gop'] for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']],
    mode='lines',
    name='GOP'
)
pop_vote_fig.add_scatter(
    x=['2008', '2012', '2016', '2020'],
    y=[sum([(x['total'] - x['dem'] - x['gop']) for x in election_data if x['year'] == y]) for y in ['2008', '2012', '2016', '2020']],
    mode='lines',
    name='Other'
)
pop_vote_fig.update_layout(
    xaxis_title_text='Year',
    yaxis_title_text='Number of votes'
)

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
            options=['2008', '2012', '2016', '2020']
        )
    ]),
    html.Br(),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dash_table.DataTable(
                id='data-table', data=election_data, 
                page_size=20, style_table={'overflowX': 'auto'}
            )
        ]),
        html.Div(className='six columns', children=[
            dcc.Graph(id='vote-share-chart', figure={})
        ])
    ]),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=[
            dcc.Graph(id='total-vote-chart', figure=pop_vote_fig)
        ])
    ])
])

@callback(
    Output(component_id='data-table', component_property='data'),
    Input(component_id='year-dropdown', component_property='value')
)
def update_table(year):
    if year is None:
        return election_data
    else:
        return [x for x in election_data if x['year'] in year]
    

@callback(
    Output(component_id='vote-share-chart', component_property='figure'),
    Input(component_id='year-dropdown', component_property='value')
)
def update_graphs(year):
    # Vote share by party for each county figure
    vote_share_fig = go.Figure()
    vote_share_fig.update_layout(
        xaxis_range=[0, 1],
        xaxis_title_text='Share of vote by party in county',
        yaxis_title_text='Frequency',
        barmode='overlay'
    )
    if year is None:
        return vote_share_fig
    else:
        vote_share_fig.add_trace(go.Histogram(
            x=[x['dem_share'] for x in election_data if x['year'] == year], name=f'Dem, {year}'
        ))
        vote_share_fig.add_trace(go.Histogram(
            x=[x['gop_share'] for x in election_data if x['year'] == year], name=f'GOP, {year}'
        ))
        vote_share_fig.update_traces(opacity=0.6)
        return vote_share_fig


# @callback(
#     Output(component_id='map', component_property='figure'),
#     Input(component_id='year-dropdown', component_property='value')
# )
# def update_map(year):
#     return year

# TODO:
# add map for county vote share
# add vote shares to nationwide popular vote figure

if __name__ == '__main__':
    app.run_server(debug=True)