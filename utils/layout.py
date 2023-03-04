from pydoc import classname
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import dash
import dash_daq as daq
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, Input, Output, callback, dash_table
import base64

from utils.dynamic_plot import dynamic_plot
img_1 = dynamic_plot()



def layout_func(table_1, table_2, payoff_table,payoff_record_table= None, type='gen'):
    
    color_dict = {"1B": "#356CA5", "2C":"#F7D507", "1D":"#8AB5E1",
              "3B":"#AB2626", "1A":"#1F4E79", "4C":"#EC9302", 
              "3A": "#7A1C1C"}
    
    if type == 'gen':
        heading_dash = "Generators Dashboard"
        placeholder_1 = 'Line capacity in MW:'
        placeholder_2 = 'Load in MW:'
        placeholder_3 = 'Generator'
    else: 
        heading_dash = "Load Dashboard"
        placeholder_1 = 'Power Generated in MW:'
        placeholder_2 = 'Line capacity in MW:'
        placeholder_3 = 'Load'
        
        
    id_gen= {
         
         'add_row_node1' : 'add_row_node1',
         'add_row_node2' : 'add_row_node2',
         'bar-chart':'bar-chart',
         'cap_constr':'cap_constr',
         'ud_demand':'ud_demand',
         'dd_demand':'dd_demand',
         'payoff_table':'payoff_table',
         'payoff_table_history':'payoff_table_history',
         'load_input':'load_input',
         'capacity_input':'capacity_input',
         'Anticipation-switch':'Anticipation-switch',
         'freeze-bids-switch':'freeze-bids-switch',
         'strategy' : 'strategy', 
         'generator_select' : 'generator_select',
         'new_table' : 'new_table',
         'mo_df_hold' : 'mo_df_hold',
         'mo_hold' : 'mo_hold',
         'dd_merit_hold' : 'dd_merit_hold',
         'ud_merit_hold' : 'ud_merit_hold',
         'rd_dem_hold' : 'rd_dem_hold',
         'clearing_price_hold' : 'clearing_price_hold',
         'strategy-text-box':'strategy-text-box',
         'sum-amount':'sum-amount',
         'text-box':'text-box',
         "sanction-input":"sanction-input",
         'display-box':'display-box',
         "sanction-output":"sanction-output",
         "img" : "img",
         "redispatch-pricing" : "redispatch-pricing",
         "save-payoff":"save-payoff",
         "flow-info":"flow-info",
         'text-summary':'text-summary'
        
         
         }
    
    id_load = id_gen.copy()
    id_load = {k: v+'-2' for k, v in id_load.items()}
    
    dash_id = id_gen if type == 'gen' else id_load
    
      
         
         
         
    # text_box_split_1 ="Monitoring aims at detecting strategic deviations of usual bidding behavior. The probability of detection of strategic bidding thus \
    # increases with the absolute deviations of the "
    
    # bold_1 =  'no game'
    
    # text_box_split_2 = "bids. The probability of detection per 1 unit of bid deviation is defined as p. Thus, the detection probability for a single actor is defined as"
    # bold_2 = "p*absolute(bid_game - bid_nogame)"
    # text_box_split_3 = " . When strategic bidding is detected, the respective bidder has to pay a monetary sanction of "
    # bold_3 = "s."
    # text_box_split_4 = "For the detection probability, we assume "
    # bold_4 =  "p=0.01"
    # text_box_split_4 = ". To see the effect of this mitigation strategy, enter a sanction here"   
    encoded_image = base64.b64encode(open('./assets/image.svg', 'rb').read()).decode()     
    app_layout = html.Div([
           
    dbc.Row(dbc.Col(html.H4(heading_dash, style={'text-align': 'center'}, className="header"),
                    width={'size': 6, 'offset': 3},
                    ),
            ),
    
    
    dbc.Row(
        [
            dbc.Col([
                 html.Div([
        
                            dash_table.DataTable(
                               id=dash_id['new_table'],
                               
                               ),
                            
                             dash_table.DataTable(
                               id=dash_id['mo_df_hold'],
                               
                               ),
                             
                              dash_table.DataTable(
                               id=dash_id['mo_hold']
                               ),
                              
                               dash_table.DataTable(
                               id=dash_id['dd_merit_hold'],
                               
                               ),
                               
                                dash_table.DataTable(
                               id=dash_id['ud_merit_hold'],
                               
                               ),
                                
                                dcc.Input(
                                id=dash_id["rd_dem_hold"]),
                                
                                
                                dcc.Input(
                                id=dash_id["clearing_price_hold"]),
                                dcc.Input(
                                id=dash_id["sum-amount"]),
                                

                            
                            ], style= {'display': 'none'} 
                            ),    
                                        html.Div(dbc.Row([
                    dbc.Col([dbc.Row([dbc.Col([
                         html.H5("Node 1"),
                         table_1,  
                         html.Div(html.Button('Add Row', id=dash_id['add_row_node1'], n_clicks=0, className="btn btn-dark"),className='button'),
                         html.Br(),
                         
                         html.Div([
                         html.P( placeholder_1 , style={'marginTop': '5px'}),
                         dcc.Input(
                            placeholder= placeholder_1,
                            type = 'number',
                            value = 5 if type == 'gen' else 9,
                            id=dash_id["capacity_input"])],
                            style={'marginTop': 10}),
                         ]),
                    
                    dbc.Col([
                         html.H5("Node 2"), 
                         table_2,  
                         html.Div(html.Button('Add Row', id=dash_id['add_row_node2'], n_clicks=0, className="btn btn-dark"),className= 'button'),
                         html.Br(),
                         
                         html.Div([
                         html.P( placeholder_2, style={'marginBottom': '0px'}),
                         dcc.Input(
                            placeholder=  placeholder_2  ,
                            type='number',
                            value=9 if type == 'gen' else 5,
                            id=dash_id["load_input"], className="Input")],
                            style={'marginTop': 10}),
                         ]),
                    html.Br(),
                    html.P(id = dash_id['text-summary'])],className='table-2-1'),
                             
                        html.Br(),
                            
                        dbc.Row([dbc.Col(dbc.Row([dbc.Col(html.P("Anticipation", className='pp_offset'), width = 3),dbc.Col(dbc.Select(
                                                                                id = dash_id['Anticipation-switch'],
                                                                                options=[
                                                                                    {"label": 'None', "value": 'No Anticipation'},
                                                                                    {"label": "Full Anticipation", "value": "Full Anticipation"},
                                                                                    {"label": "Bayesian Equilibrium", "value": "Bayesian Equilibrium"},    
                                                                                    ],
                                                                                value = 'No Anticipation' ,
                                        ),width =6)]),className = 'dropdown_align'),  
                                 dbc.Col(dbc.Row([dbc.Col(html.P("Redispatch pricing", className='pp_offset'), width = 3),dbc.Col(dbc.Select(
                                                                                id = dash_id["redispatch-pricing" ],
                                                                                options=[
                                                                                    {"label": 'Uniform Pricing', "value": 'uniform pricing'},
                                                                                    {"label": "pay-as-bid", "value": "pay-as-bid"},
                                                                                       
                                                                                    ],
                                                                                value = 'uniform pricing' ,
                                        ),width =6)]),className = 'dropdown_align'),  


                                dbc.Col(     
                                    daq.BooleanSwitch(
                                    on=False,
                                    id=dash_id['freeze-bids-switch'],
                                    label="Freeze bids",
                                    className = "custom-control-input",
                                    labelPosition="top"
                                    ), width =2),
                             
                            ],className='text-dd'),
                            
                        html.Br(),
                        
                        
                        dbc.Row([
                        dbc.Col([html.H5("Payoff Table"),
                          
                        payoff_table,
                        html.Div(html.Button('Save', id=dash_id['save-payoff'], n_clicks=0, className="btn btn-dark"),className='button'),
                        
                         
                         ])], className = 'table-2-1'),
                        
                        html.Br(),
                        
                        dbc.Row([   html.H5("Mitigation Strategy"),
                                    dbc.Col(dbc.Row([dbc.Col(html.P("Strategy", className='p_offset'), width = 3),dbc.Col(dbc.Select(
                                                                                id = dash_id['strategy'],
                                                                                options=[
                                                                                    {"label": 'None', "value": 'do_nothing'},
                                                                                        {"label": "Stochastic Non-Attribution", "value": "Stochastic Non-Attribution"},
                                                                                        {"label": "Monitoring and Penalization", "value": "Monitoring and Penalization"},
                                                                                        {"label": "Capacity Pricing", "value": "Capacity Pricing"},
                                                                                        
                                                                                    ],
                                                                                value = 'do_nothing' ,
                                    ),width =4)]),className = 'dropdown_align'),
                                    dbc.Col(dbc.Row([dbc.Col(html.P(placeholder_3,className='p_offset'), width = 3),dbc.Col(dbc.Select(
                                                                                id = dash_id['generator_select'],
                                                                                value =  None,
                                                                                
                                    ),width =4)]),className = 'dropdown_align'),
                                    html.Br(),
                                    html.Div(id =dash_id['display-box'],children = [html.Span(id=dash_id['text-box'], className='text_box'),dcc.Input(
                                    type='number',
                                    value= 1000,
                                    id = dash_id["sanction-input"], className="Input"),html.Span(" €"),html.Br(),
                                    html.Br(),
                                    html.P(id = dash_id["sanction-output"], className='text_box'), 
                                    ], style= {'display': 'none'}),
                                    html.Br(),
                                    html.P(id=dash_id['strategy-text-box'], className='text_box'),
                                    html.Img(id = dash_id['img'],src="./assets/image.jpg", style={'display': 'none', 'height':'40%', 'width':'55%', 'text-align':'center' })
                                ],className='text-dd'),
                        
                       
                            
                    ]),
                    # "data:image/svg;base64,{}".format(encoded_image)
                    dbc.Col([html.Div(dbc.Row(dcc.Graph(id=dash_id['bar-chart'], figure={})), className = 'graph-layout'),
                             html.Div([
                 html.P(id=dash_id['cap_constr']),
                 html.Br(),
                 html.P(id=dash_id['dd_demand']),
                 html.Br(),
                 html.P(id=dash_id['ud_demand'])], className='text-dd')
                             
                             ])

                    ],align="start"), className= 'main_layout'), 
                
                    ]),
            
        ],align="center"),
          html.Br(),
            
         dbc.Row([html.H5("Payoff History"),
                                 payoff_record_table,
                                 
                                 ],className='table-2-1'
                                ),
         html.Br()
            ])

    return app_layout



def layout_func_home():
    
    id_dct = {}
    heading_dash = "Background Info"  
    background_info = "This dashboard is an interactive tool for the analysis and intuitive visualization of the incentives for inc-dec gaming under different scenarios. Theryby, different mitigation" \
                        + " strategies and two redispatch pricing mechanisms can be tested in a generator's dashboard and a load dashboard, representing the behavior of flexible generators or flexible loads."  
    app_layout = html.Div([
    
    
      
    dbc.Row([dbc.Col(html.H2(heading_dash, style={'text-align': 'center'}, className="top_header"),
                    width={'size': 6, 'offset': 3},
                    ),
            ]
            ),
    dbc.Row(dbc.Col(html.P(background_info, style={'text-align': 'center','font-size':'130%'}, className="header"),
                    width={'size': 8, 'offset': 2}
                    
                    )),
    

    dbc.Row(
        [
            dbc.Col([
                    
                    html.Div(dbc.Row([
                    dbc.Col([dbc.Row([
                    html.Br(),
                    html.P("1st box")],className='table-2-1'),
                             
                        html.Br(),
                            
                        dbc.Row([html.P("2nd box")],className='text-dd'),
                            
                        html.Br(),
                        
                        
                        dbc.Row([
                        dbc.Col([html.H5("Payoff Table"),
                         ])], className = 'table-2-1'),
                        
                        html.Br(),
                        
                        dbc.Row([   html.H5("3rd box"),],className='text-dd'),
                        
                       
                            
                    ]),
                    
                    dbc.Col([html.Div(dbc.Row(html.H5("4th box")), className = 'text-dd'),
                              html.Br(),
                             html.Div([ html.H5("5th box")], className='text-dd')
                             
                             ])

                    ],align="start"), className= 'main_layout'), 
                
                    ]),
            
        ],align="center"),
          html.Br(),
         html.Br()
            ])
    return app_layout
    
        
