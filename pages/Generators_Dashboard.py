# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 10:10:20 2022

@author: VRegener
"""

from operator import index
from pydoc import classname
from matplotlib.pyplot import table
import itertools
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import dash
import os
import dash_bootstrap_components as dbc
from sklearn.manifold import trustworthiness
from utils.layout import layout_func
from utils.strategies import strategies_sel
from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, Input, Output, callback

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
dash.register_page(__name__,path='/')

import numpy as np
from utils.functions import redispatch, payoffs, game, return_table
from utils.plot import plot_function


# -----------------------------------------------------------------------------
# Default Inputs
bool_var = True
merit_order_df = 0
c = 1
counter = 1
input_data = {'cap': [3,3,3,3,3,3], # production capacities of generators
              'cost': [40,0.1,35,30,45,50], # marginal costs of generators
              'node': [1,1,1,2,2,2], # generator location (1: export costr. node; 2: import constr. node)
              'Game': [True,True,True,True,True,True]} # Allow, or forbid strategic bidding


# input_data = {'cap': [2.5,2.5,2.5,2.5], # production capacities of generators
#                 'cost': [25,41.666667,58.333,75.0], # marginal costs of generators
#                 'node': [2,2,1,1], # generator location (1: export costr. node; 2: import constr. node)
#                 'Game': [True,True,True,True]}

markup = 0
type = 'gen'

# generate input dataframe
input_df = pd.DataFrame(input_data)
input_df  = input_df.replace(0, 0.0001)
input_df['name'] = [f"G{i+1}" for i in range(len(input_df))]

# create dataframes for both nodes
node1_df = input_df[['name','cap','cost','Game']][input_df.node == 1]
node2_df = input_df[['name','cap','cost','Game']][input_df.node == 2]
payoff_df = pd.DataFrame(columns = input_df['name'])


# convert dataframes to editable dash tables
cols = [
        dict(id='name', name='name'),
        dict(id='cap', name='cap', type='numeric'),
        dict(id='cost', name='cost', type='numeric'),
        dict(id='Game', name='Game')]
cols_payoff_df = [
        {"name": i, "id": i} for i in sorted(payoff_df.columns)
    ]


table_1 = return_table('node1_table',node1_df,cols)
table_2 = return_table('node2_table',node2_df,cols)
table_3 = return_table('payoff_table_history')
payoff_table = return_table('payoff_table')

# -----------------------------------------------------------------------------
# App layout

layout = layout_func(table_1, table_2,payoff_table,table_3)


# ----------------------------------------------------------------------------- 
# mo_df, mo, dd_merit,ud_merit, rd_dem, clearing price 
# Create Graphs
@callback(
    Output(component_id='new_table', component_property='data'),
    Output(component_id='mo_df_hold', component_property='data'),
    Output(component_id='mo_hold', component_property='data'), 
    Output(component_id='dd_merit_hold', component_property='data'), 
    Output(component_id='ud_merit_hold', component_property='data'),
    Output(component_id='rd_dem_hold', component_property='value'),
    Output(component_id='clearing_price_hold', component_property='value'), 
    Output(component_id='sum-amount', component_property='value'),  
    
     Input(component_id='node1_table', component_property='data'),
     Input(component_id='node1_table', component_property='columns'),
     Input(component_id='node2_table', component_property='data'),
     Input(component_id='node2_table', component_property='columns'),
     
     Input(component_id='load_input', component_property='value'),
     Input(component_id='capacity_input', component_property='value'),
     Input(component_id='Anticipation-switch', component_property='value'),
     Input(component_id='freeze-bids-switch', component_property='on'),
     Input(component_id='redispatch-pricing', component_property='value'),
     Input('save-payoff', 'n_clicks'),
     )


def update_graph(data1, columns1, data2, columns2, load_mw, capacity_mw, anticipation, on_freeze,redispatch_pricing,n_clicks):
    '''
    Parameters
    ----------
    data1 : dash table
        table containing merit order for node 1
    columns1 : dash table columns
        table column names from node 1
    data2 : dash table
        table containing merit order for node 1
    columns2 : dash table columns
        table column names from node 1
    load_mw : numeric
        load in MW located at node 2
    capacity_mw : numeric
        grid capacity in MW between node 1 and 2
    anticipation : String
        selects if strategic biddig is enabled ('Mit Antizipation') or not ('Ohne Antizipation').

    Raises
    ------
    dash
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    '''
    
    # check if tables complete
    
    if any([not all(d.values()) for d in data1]) or any([not all(d.values()) for d in data2]):
        raise dash.exceptions.PreventUpdate
    
    # convert dash tables to dataframes
    node1_df = pd.DataFrame(data=data1, columns = [col['name'] for col in columns1])
    node1_df['node'] = [1]*len(data1)
    node2_df = pd.DataFrame(data=data2, columns = [col['name'] for col in columns2])
    node2_df['node'] = [2]*len(data2)
    
    # concateante both dataframes and extend by bid column
    input_df = pd.concat([node1_df,node2_df])
    input_df['bid'] = input_df.cost+markup
    input_df.set_index(['name'],inplace=True)
    
    global c
    c= c
    global counter
    counter = counter
    
    global bool_var
    bool_var = bool_var
    global merit_order_df
    merit_order_df = merit_order_df
    if n_clicks == 0:
        counter = 1    
    # create merit order
    mo = input_df.sort_values(by='bid')
    # mo['x_pos'] = mo.cap.cumsum() - 0.5*mo.cap
    mo['mark'] = 0
    if anticipation == 'No Anticipation':
        bool_var = True
    
    # calculate redispatch
    if bool_var:
        mo_1,mo_2,rd_dem,dd_price,ud_price = redispatch(mo=mo, load=load_mw, line_cap=capacity_mw, anticipation =anticipation,pay_as_bid = redispatch_pricing, freeze_bool = 'False')
        dd_merit = mo_1[mo_1.disp > 0]
        ud_merit = mo_2[mo_2.disp < mo_2.cap]   
        mo_df = pd.concat([mo_1,mo_2])
        mo_df.sort_values(by='bid', inplace=True)
        mo_df['left_to_disp'] = mo_df.cap- mo_df.disp
        mo_left_for_disp = mo_df[mo_df.left_to_disp > 0]
        mo_left_for_down_disp = mo_df[mo_df.disp>0].sort_values(by='bid',ascending=False)
         

        
        clearing_price= mo_df.bid[mo_df.cap.cumsum()>=load_mw].min()
        production_line_flow = mo_df[mo_df.node==1]['disp'].sum()
        
        min_node_2_cost = mo_df[mo_df.node==2]
        print(min_node_2_cost.head())
        
        min_node_2_cost = min_node_2_cost[min_node_2_cost.disp==0]
        try:
            min_node_2_cost = min_node_2_cost.iloc[0, min_node_2_cost.columns.get_loc('bid')]
        except:
            min_node_2_cost = 0
        max_node_1_cost = mo_df[mo_df.node==1]
        max_node_1_cost = max_node_1_cost[max_node_1_cost.disp!=0]
        try:
            max_node_1_cost = max_node_1_cost.iloc[-1, max_node_1_cost.columns.get_loc('bid')]
        except:
            max_node_1_cost = 0
       
        mo_df['real_cost'] = mo_df['cost']
        mo_df['prod'] = mo_df.disp + mo_df.rd
        mo_df['payoff_without_anticipated'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = 'gen',redispatch_pricing = redispatch_pricing,sel = None,capacity_pricing = False),axis=1)
        x= mo_df['payoff_without_anticipated']
        
    
        d = {} 
        
        mo_df = mo_df.reset_index()
        l1 =mo_df.name.tolist()
        
        l2 = [mo_df.payoff_without_anticipated.tolist()]
        if os.path.exists("./payoff_export_dataframe.csv"):
            if c == 1:
                    os.remove("./payoff_export_dataframe.csv")
                    
            elif n_clicks == 0 :
                os.remove("./payoff_export_dataframe.csv")
                
        
        mo_df = mo_df.set_index('name')
        if counter-n_clicks<=0:
            
            if os.path.exists("./payoff_export_dataframe.csv"):
                payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
                for i in l1:
                    if i not in payoff_export_dataframe.columns.tolist():
                        r = ["Not Available" for i in range(len(payoff_export_dataframe))]
                        pos = len(payoff_export_dataframe.columns)-2
                        payoff_export_dataframe.insert(pos,i,r)
                
                    
                
                mo_df_dup = mo_df.reset_index()
                mo_df_dup = mo_df_dup.sort_values('name')
                l1 = mo_df_dup.name.tolist()
                l2 = mo_df_dup.payoff_without_anticipated.tolist()
                li = [None,None,None,None,None]  + [str(i)+"€" for i in l2] + [None,None]            
                payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
                
                payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
            
            
            else:
                l2 = [[str(i)+"€" for i in x] for x in l2] 
                payoff_export_dataframe = pd.DataFrame(l2 , columns= l1)
                payoff_export_dataframe = payoff_export_dataframe.sort_index(axis=1)
                l1 = sorted(l1)        
                payoff_export_dataframe["Load(MW)"] = ""
                payoff_export_dataframe["Line Capacity(MW)"] = ""
                payoff_export_dataframe["Anticipation"] = ""
                payoff_export_dataframe["Redispatch Pricing"] = ""
                payoff_export_dataframe["Mitigation Strategy"] = ""
                payoff_export_dataframe["Redispatch Payment"] = None
                payoff_export_dataframe["Total Costs"] = None
                new_cols = ["Load(MW)","Line Capacity(MW)","Anticipation","Redispatch Pricing","Mitigation Strategy",*l1,"Redispatch Payment","Total Costs"]  
                payoff_export_dataframe = payoff_export_dataframe[new_cols]    
                payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
                c = c + 1
    
    freeze_bool = '{}'.format(on_freeze)

    # adjust bids strategically if anticipation is true
    if anticipation != 'No Anticipation':
    

        if bool_var:
            max_bid = mo_df.cost.max()
            min_bid = mo_df.cost.min()
            
            data_frame= mo_df.apply(lambda x : game(x,mo_left_for_disp,mo_left_for_down_disp,max_node_1_cost,min_node_2_cost,line_capacity = capacity_mw,udp=ud_price,ddp=dd_price,production_line_flow = production_line_flow,
                                                       markup=0, strat=anticipation,
                                                       x_max=max_bid, x_min=min_bid,redispatch_pricing=redispatch_pricing), axis = 1)   
            
            
            bid =[]
            cost =[]
            real_cost = [] 
            mark = []
            for i in data_frame:
                bid.append(i[0])
                cost.append(i[1])
                real_cost.append(i[2])
                mark.append(i[3])
           
            mo_df['bid'],mo_df['cost'],mo_df['real_cost'],mo_df['mark'] = bid,cost,real_cost,mark
            merit_order_df = mo_df
           
            
        mo_df = merit_order_df
       
        # if redispatch_pricing == 'pay-as-bid':
        #     mo_df['bid'] = mo_df['red_bid'] 
        
        mo_df.sort_values(by='bid',inplace=True)
       
        mo_df['cap'] = mo['cap']
        # mo_df['cost'] = mo['cost']
        mo_df['Game'] = mo['Game']
        mo_df['x_pos'] = mo_df.cap.cumsum() - 0.5*mo_df.cap
        
        # calculate redispatch for anticipated bidding 
        mo_1,mo_2,rd_dem,dd_price,ud_price = redispatch(mo=mo_df, load=load_mw, line_cap=capacity_mw,anticipation =anticipation, pay_as_bid = redispatch_pricing)
        
        dd_merit = mo_1[mo_1.disp > 0]
        ud_merit = mo_2[mo_2.disp < mo_2.cap]       
        mo_df = pd.concat([mo_1,mo_2])
        
        
        mo_df.sort_values(by='bid', inplace=True)
        clearing_price= mo_df.bid[mo_df.cap.cumsum()>=load_mw].min()
        mo_df['prod'] = mo_df.disp + mo_df.rd
        mo_df['payoff_anticipated'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = 'gen', redispatch_pricing=redispatch_pricing,sel = None,capacity_pricing = False),axis=1)
        
        mo_df_dup = mo_df.reset_index()
        mo_df_dup = mo_df_dup.sort_values('name')
        l1 = mo_df_dup.name.tolist()
        l2 = mo_df_dup.payoff_anticipated.tolist()
        li = [None,None,None,None,None] + [str(i)+"€" for i in l2] + [None,None]
        if os.path.exists("./payoff_export_dataframe.csv") and counter-n_clicks<=0:
            payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
            payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
            payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
        
        
        
        if freeze_bool == 'True':
            bool_var = False
        elif freeze_bool == 'False':
            bool_var = True
    
                  
    # Dynamic select button
    if anticipation != 'No Anticipation':
        
        mo_game = mo_df[mo_df.cost != mo_df.bid] 
        mo_notgame = mo_df[mo_df.cost == mo_df.bid].reset_index() 
        mo_game = mo_game.reset_index()
        mo_game['name'] = mo_game['name'] + '(Game)' 
        
        mo_game = pd.concat([mo_game,mo_notgame]) 
        
        mo_final = mo_game
    
    else:
        mo_final= pd.DataFrame(columns=['name'])
        

    # calculate spot market clearing price
    mo_df.sort_values(by='bid', inplace=True)

    clearing_price= mo_df.bid[mo_df.cap.cumsum()>=load_mw].min()

    mo_df = pd.concat([mo_df.drop('cap',axis =1,inplace = False), input_df['cap']], axis=1, join="inner")
    mo_df.reset_index(inplace=True)
    mo.reset_index(inplace=True)
    dd_merit.reset_index(inplace= True)
    ud_merit.reset_index(inplace = True)
    print("ud_merit")
    print(ud_merit.head())
    ud_merit = ud_merit.astype({'red_bid': 'int','cost': 'int','red_bid': 'int'})
    dd_merit = dd_merit.astype({'red_bid': 'int','cost': 'int','red_bid': 'int'})
    sum_amount_with_strategy  = rd_dem * ud_price -  rd_dem * dd_price
    if redispatch_pricing == "pay-as-bid":
        sum_amount_with_strategy  = (mo_df['rd']* mo_df['red_bid']).sum()
        
    mo_df = mo_df.to_dict('records')
    mo = mo.to_dict('records')
    dd_merit['color'] = "#356CA5"
    ud_merit['color'] = "#EC9302"
    # print(mo_final.head())
    dd_merit = dd_merit.to_dict('records')
    ud_merit = ud_merit.to_dict('records')
    mo_final = mo_final.to_dict('records')
    
    return mo_final, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price,sum_amount_with_strategy
    

# callback for select button
@callback(
    Output(component_id='generator_select', component_property='options'),
    Input(component_id='new_table', component_property='data'),
    Input(component_id='strategy', component_property='value'),)
def add_select_options(data,strategy_sel):
    
    data = pd.DataFrame(data)
    if data.empty:
        data = pd.DataFrame(columns=['name'])
   
    # col_name = [i.split('(')[0] for i in data.name.tolist()]
    col_name = data.name.tolist()
    # combinations = []
    # for r in range(len(col_name)+1):
    #     for combination in itertools.combinations(col_name, r):
    #         combinations.append(combination)
            
    # print(combinations)
    
    dict_select =[{'label': 'None', 'value': None}] + [{'label': i, 'value': i} for i in col_name] 
    return dict_select


    
# callback for strategies
@callback(
    Output(component_id='bar-chart', component_property='figure'),
    Output(component_id='ud_demand', component_property='children'),
    Output(component_id='dd_demand', component_property='children'),
    Output(component_id='payoff_table', component_property='data'),
    Output(component_id='payoff_table_history', component_property='data'),
    Output(component_id='cap_constr', component_property='children'),
    Output(component_id='strategy-text-box', component_property='children'),
    Output(component_id='text-box', component_property='children'),
    Output(component_id='display-box', component_property='style'),
    Output(component_id='img', component_property='style'),
    Output(component_id='sanction-output',  component_property='children'),
    Output(component_id='text-summary',  component_property='children'),
    
   
    
    
    Input(component_id='generator_select', component_property='value'),
    Input(component_id='strategy', component_property='value'),
    Input(component_id='load_input', component_property='value'),
    Input(component_id='mo_df_hold', component_property='data'),
    Input(component_id='mo_hold', component_property='data'), 
    Input(component_id='dd_merit_hold', component_property='data'), 
    Input(component_id='ud_merit_hold', component_property='data'),
    Input(component_id='rd_dem_hold', component_property='value'),
    Input(component_id='clearing_price_hold', component_property='value'),
    Input(component_id='capacity_input', component_property='value'),
    Input(component_id='Anticipation-switch', component_property='value'),
    Input(component_id='sum-amount', component_property='value'),
    Input(component_id='sanction-input', component_property='value'),
    Input(component_id='redispatch-pricing', component_property='value'),
    Input('save-payoff', 'n_clicks'),
       
    )
def strategies_select(gen_sel, strategy,load_mw, mo_df, mo, dd_merit,ud_merit, rd_dem, clearing_price,capacity_mw, anticipation,sum_amount_without_strategy,sanction,redispatch_pricing,n_clicks):
    
    global counter
    counter = counter
    fig,  print_ud, print_dd, payoff_table, payoff_export_dataframe,cap_cons,strategy_box_text,text_box, style,style_1,sanction_output,counter,text_summary_box = strategies_sel(gen_sel, strategy,load_mw, mo_df, mo, dd_merit,ud_merit, rd_dem, clearing_price,capacity_mw,sum_amount_without_strategy, sanction,n_clicks,counter,anticipation, 'gen', redispatch_pricing= redispatch_pricing,return_dataframe=False)
    
    return fig,  print_ud, print_dd, payoff_table,payoff_export_dataframe,cap_cons,strategy_box_text,text_box,style,style_1,sanction_output,text_summary_box
# callback to edit table at node 1
@callback(
    Output('node1_table', 'data'),
    Input('add_row_node1', 'n_clicks'),
    State('node1_table', 'data'),
    State('node1_table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

# callback to edit table at node 2
@callback(
    Output('node2_table', 'data'),
    Input('add_row_node2', 'n_clicks'),
    State('node2_table', 'data'),
    State('node2_table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows



