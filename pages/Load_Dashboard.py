# -*- coding: utf-8 -*-
"""
Created on Thu Mar  3 10:10:20 2022

@author: VRegener
"""

from re import L
import os
from utils.plot import plot_function
from utils.functions import redispatch_load as redispatch, payoffs, game, return_table
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import dash
import dash_bootstrap_components as dbc
from utils.layout import layout_func
from utils.strategies import strategies_sel
from utils.layout import layout_func
from dash.dependencies import Input, Output, State
from dash import Dash, dcc, html, Input, Output, callback


dash.register_page(__name__)


# -----------------------------------------------------------------------------
# Default Inputs

bool_var = True
type = 'load'
c =1
counter = 1
color_dict = {"1B": "#356CA5", "2C": "#F7D507", "1D": "#8AB5E1",
              "3B": "#AB2626", "1A": "#1F4E79", "4C": "#EC9302",
              "3A": "#7A1C1C"}
merit_order_df = 0
input_data = {'Load': [3, 3, 3, 3, 3, 3],  # production capacities of generators
              'WTP': [35, 10, 40, 30, 45, 50],  # marginal costs of generators
              # generator location (1: export costr. node; 2: import constr. node)
              'Node': [1, 1, 1, 2, 2, 2],
              'Game': [True, True, True, True, True, True]}

# # Allow, or forbid strategic bidding
# input_data = {'Load': [1.25, 1.25, 1.25, 1.25, 1.25, 1.25,1.25,1.25],  # production capacities of generators
#                   'WTP': [100, 85.71, 71.42,57.14, 42.85, 28.57, 14.28,0],  # marginal costs of generators
#                   # generator location (1: export costr. node; 2: import constr. node)
#                   'Node': [2, 2, 2,2,1, 1, 1,1 ],
#                   'Game': [True, True, True, True, True,True, True, True]}  # Allow, or forbid strategic bidding 
# # markups to set bids above marginal costs


# input_data = {'Load': [2.5, 2.5, 2.5, 2.5],  # production capacities of generators
#                   'WTP': [50,50,50,50],  # marginal costs of generators
#                   # generator location (1: export costr. node; 2: import constr. node)
#                   'Node': [2, 2, 1,1 ],
#                   'Game': [True, True, True, True]} 
markup = 0

# generate input dataframe
input_df = pd.DataFrame(input_data)
input_df  = input_df.replace(0, 0.0001)
input_df['Name'] = [f"L{i+1}" for i in range(len(input_df))]

# create dataframes for both nodes
node1_df = input_df[['Name', 'Load', 'WTP', 'Game']][input_df.Node == 1]
node2_df = input_df[['Name', 'Load', 'WTP', 'Game']][input_df.Node == 2]
payoff_df = pd.DataFrame(columns=input_df['Name'])

print(input_df.head())
# convert dataframes to editable dash tables
cols = [
    dict(id='Name', name='Name'),
    dict(id='Load', name='Load', type='numeric'),
    dict(id='WTP', name='WTP', type='numeric'),
    dict(id='Game', name='Game')]
cols_payoff_df = [
    {"Name": i, "id": i} for i in sorted(payoff_df.columns)
]


table_1 = return_table('node1_table-2', node1_df, cols)
table_2 = return_table('node2_table-2', node2_df, cols)
table_3 = return_table('payoff_table_history-2')
payoff_table = return_table('payoff_table-2')

# -----------------------------------------------------------------------------
# App layout
layout = layout_func(table_1, table_2, payoff_table, table_3, type='load')


# -----------------------------------------------------------------------------
#Output(component_id='generator_select-2', component_property='options'),

# Create Graphs
@callback(
    Output(component_id='new_table-2', component_property='data'),
    Output(component_id='mo_df_hold-2', component_property='data'),
    Output(component_id='mo_hold-2', component_property='data'),
    Output(component_id='dd_merit_hold-2', component_property='data'),
    Output(component_id='ud_merit_hold-2', component_property='data'),
    Output(component_id='rd_dem_hold-2', component_property='value'),
    Output(component_id='clearing_price_hold-2', component_property='value'),
    Output(component_id='sum-amount-2', component_property='value'),
    


    Input(component_id='node1_table-2', component_property='data'),
    Input(component_id='node1_table-2', component_property='columns'),
    Input(component_id='node2_table-2', component_property='data'),
    Input(component_id='node2_table-2', component_property='columns'),
    
    Input(component_id='capacity_input-2', component_property='value'),
    Input(component_id='load_input-2', component_property='value'),
    Input(component_id='Anticipation-switch-2', component_property='value'),
    Input(component_id='freeze-bids-switch-2', component_property='on'),
    Input(component_id='redispatch-pricing-2', component_property='value'),
    Input('save-payoff-2', 'n_clicks'),)

def update_graph(data1_2, columns1_2, data2_2, columns2_2, power_mw, capacity_mw, anticipation, on_freeze,redispatch_pricing,n_clicks):
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
    power_mw : numeric
        Power available in MW located at node 1
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
    if any([not all(d.values()) for d in data1_2]) or any([not all(d.values()) for d in data2_2]):
        raise dash.exceptions.PreventUpdate

    # convert dash tables to dataframes
    node1_df = pd.DataFrame(data=data1_2, columns=[
                            col['name'] for col in columns1_2])
    node1_df['Node'] = [1]*len(data1_2)
    node2_df = pd.DataFrame(data=data2_2, columns=[
                            col['name'] for col in columns2_2])
    node2_df['Node'] = [2]*len(data2_2)
    #anticipation =  '{}'.format(on_anticipation)

    # concateante both dataframes and extend by bid column
    input_df = pd.concat([node1_df, node2_df])
    input_df['bid'] = input_df.WTP+markup
    input_df.set_index(['Name'], inplace=True)
    print(input_df.head())
    
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

#    create merit order
    mo = input_df.sort_values(by='bid', ascending=False)
   
    if anticipation == 'No Anticipation':
        bool_var = True

    if bool_var:
        print("asdasdasdasdasdasdasdasd")
        mo_1, mo_2, rd_dem, dd_price, ud_price = redispatch(
            mo=mo, power=power_mw, line_cap=capacity_mw,pay_as_bid = redispatch_pricing, freeze_bool = 'False')
        print("Inside load_dashboard main function")
        
        if redispatch_pricing == 'pay-as-bid':
            mo_1.red_bid = mo_1.pay_as_bid_red
            mo_2.red_bid = mo_2.pay_as_bid_red
        dd_merit = mo_2[mo_2.disp > 0]
        ud_merit = mo_1[mo_1.disp < mo_1.Load]
        mo_df = pd.concat([mo_1, mo_2])
        
        mo_df.sort_values(by='bid', inplace=True, ascending=False)
        clearing_price = mo_df.bid[mo_df.Load.cumsum() >= power_mw].max()
        production_line_flow = mo_df[mo_df.Node==2]['disp'].sum()
        print("production_line_flow: ", production_line_flow)
        mo_df['left_to_receive'] = mo_df.Load- mo_df.disp
        mo_left_to_receive = mo_df[mo_df.left_to_receive > 0]
        mo_left_not_to_receive = mo_df[mo_df.disp>0]
        
        
        min_node_2_cost = mo_df[mo_df.Node == 2]
        min_node_2_cost = min_node_2_cost[min_node_2_cost.disp !=0] 
        try: 
            min_node_2_cost = min_node_2_cost.iloc[-1, min_node_2_cost.columns.get_loc('bid')]
        except:
            min_node_2_cost = 0
          
        max_node_1_cost = mo_df[mo_df.Node==1]
        max_node_1_cost = max_node_1_cost[max_node_1_cost.disp< max_node_1_cost.Load]
        try:
            max_node_1_cost = max_node_1_cost.iloc[0, max_node_1_cost.columns.get_loc('bid')]   
        except:
            max_node_1_cost = 0
        
        
        
        mo_df['real_WTP'] = mo_df['WTP'].copy()
        mo_df['power_receive'] = mo_df.disp + mo_df.rd
        mo_df['payoff_without_anticipated'] = mo_df.apply(lambda x: payoffs(
            x, cp=clearing_price, udp=ud_price, ddp=dd_price, type='load' ,redispatch_pricing=redispatch_pricing,sel = None,capacity_pricing = False), axis=1)
        
        d = {} 
        
        mo_df = mo_df.reset_index()
        l1 =mo_df.Name.tolist()
        l2 = [mo_df.payoff_without_anticipated.tolist()]
        if os.path.exists("./payoff_export_dataframe.csv"):
            if c == 1:
                    os.remove("./payoff_export_dataframe.csv")
                    
            elif n_clicks == 0 :
                os.remove("./payoff_export_dataframe.csv")
                
        mo_df = mo_df.set_index('Name')
        
        
        if counter-n_clicks<=0:
            if os.path.exists("./payoff_export_dataframe.csv"):
                
                
                payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
                
                for i in l1:
                    if i not in payoff_export_dataframe.columns.tolist():
                        r = ["Not Available" for i in range(len(payoff_export_dataframe))]
                        pos = len(payoff_export_dataframe.columns)-2
                        payoff_export_dataframe.insert(pos,i,r)
                                 
                mo_df_dup = mo_df.reset_index()
                mo_df_dup = mo_df_dup.sort_values('Name')
                l1 = mo_df_dup.Name.tolist()
                l2 = mo_df_dup.payoff_without_anticipated.tolist()
                li = [None,None,None,None,None]  + [str(i)+"€" for i in l2]  + [None,None] 
                          
                payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
                
                
                payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
            
            
            else: 
                l2 = [[str(i)+"€" for i in x] for x in l2] 
                payoff_export_dataframe = pd.DataFrame(l2, columns= l1)
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
                payoff_export_dataframe["Total Costs"] = None
                payoff_export_dataframe["Redispatch Payment"] = None
                payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
               
                c = c + 1
    freeze_bool = '{}'.format(on_freeze)
    
    # adjust bids strategically if anticipation is true
    if anticipation != 'No Anticipation':

        if bool_var:
            max_bid = mo_df.WTP.max()
            min_bid = mo_df.WTP.min()
            # min_node_2_cost,line_capacity = capacity_mw,udp=ud_price,ddp=dd_price,production_line_flow = production_line_flow,
            data_frame = mo_df.apply(lambda x: game(x,mo_left_for_disp=mo_left_to_receive,mo_left_for_down_disp=mo_left_not_to_receive, max_node_1_cost = max_node_1_cost,min_node_2_cost = min_node_2_cost, line_capacity = 5, udp=ud_price, ddp=dd_price,production_line_flow = production_line_flow,
                                                      markup=0, type='load', strat=anticipation,
                                                      x_max=max_bid, x_min=min_bid,redispatch_pricing=redispatch_pricing), axis=1)
            bid =[]
            cost =[]
            real_cost = [] 
            mark = []
            for i in data_frame:
                bid.append(i[0])
                cost.append(i[1])
                real_cost.append(i[2])
                mark.append(i[3])
           
            mo_df['bid'],mo_df['WTP'],mo_df['real_WTP'],mo_df['mark'] = bid,cost,real_cost,mark
            merit_order_df = mo_df
            
         
          

        mo_df = merit_order_df
        mo_df.sort_values(by='bid', inplace=True, ascending=False)
        mo_df['Load'] = mo['Load']
        # mo_df['WTP'] = mo['WTP']
        mo_df['Game'] = mo['Game']
        mo_df['x_pos'] = mo_df.Load.cumsum() - 0.5*mo_df.Load

        # calculate redispatch for anticipated bidding
        mo_1, mo_2, rd_dem, dd_price, ud_price = redispatch(
            mo=mo_df, power=power_mw, line_cap=capacity_mw)
        
        if redispatch_pricing == 'pay-as-bid':
            mo_1.red_bid = mo_1.pay_as_bid_red
            mo_2.red_bid = mo_2.pay_as_bid_red
            
        dd_merit = mo_2[mo_2.disp > 0]
        ud_merit = mo_1[mo_1.disp < mo_1.Load]
        mo_df = pd.concat([mo_1, mo_2])
        # print("After")
        # print(mo_df.head(6))
        mo_df.sort_values(by='bid', inplace=True, ascending=False)
        clearing_price = mo_df.bid[mo_df.Load.cumsum() >= power_mw].max()
        mo_df['power_receive'] = mo_df.disp + mo_df.rd
        mo_df['payoff_anticipated'] = mo_df.apply(lambda x: payoffs(
            x, cp=clearing_price, udp=ud_price, ddp=dd_price, type='load', redispatch_pricing=redispatch_pricing,sel = None,capacity_pricing = False), axis=1)

        
        mo_df_dup = mo_df.reset_index()
        mo_df_dup = mo_df_dup.sort_values('Name')
        l1 = mo_df_dup.Name.tolist()
        l2 = mo_df_dup.payoff_anticipated.tolist()
        li = [None,None,None,None,None]  + [str(i)+"€" for i in l2] + [None,None]
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

        mo_game = mo_df[mo_df.WTP != mo_df.bid]
        mo_notgame = mo_df[mo_df.WTP == mo_df.bid].reset_index() 
        mo_game = mo_game.reset_index()
        mo_game['Name'] = mo_game['Name'] + '(Game)'
        mo_game = pd.concat([mo_game,mo_notgame]) 
        mo_final = mo_game

    else:
        mo_final = pd.DataFrame(columns=['Name'])

    mo_df.sort_values(by='bid', inplace=True, ascending=False)

    clearing_price = mo_df.bid[mo_df.Load.cumsum() >= power_mw].max()

    mo_df = pd.concat([mo_df.drop('Load', axis=1, inplace=False),
                      input_df['Load']], axis=1, join="inner")
    mo_df.reset_index(inplace=True)
    mo.reset_index(inplace=True)
    dd_merit.reset_index(inplace=True)
    ud_merit.reset_index(inplace=True)
    
    l =[]
    for i in dd_merit.iterrows():
        
        if i[1]['red_bid'] != i[1]['WTP']:
            s = str(i[1]['Name']) + " bids " + str(i[1]['red_bid']) + " €/MWh at the redispatch market instead of their marginal cost of " + str(i[1]['WTP']) + " €/MWh adjusting their <br> bid towards the anticipated market clearing price to maximize their payoff."
            l.append(s)
        else:
            l.append("<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh")
    dd_merit.hover_template = l       
    l=[]
    # print("ud_merit")
    # print(ud_merit.head())
    ud_merit = ud_merit.astype({'red_bid': 'int','WTP': 'int','pay_as_bid_red': 'int'})
    dd_merit = dd_merit.astype({'red_bid': 'int','WTP': 'int','pay_as_bid_red': 'int'})
    for i in ud_merit.iterrows():
        if i[1]['red_bid'] != i[1]['WTP']:
            s = str(i[1]['Name']) + " bids " + str(i[1]['red_bid']) + " €/MWh at the redispatch market instead of their marginal cost of " + str(i[1]['WTP']) + " €/MWh adjusting their <br> bid towards the anticipated market clearing price to maximize their payoff."
            l.append(s)
        else:
            l.append("<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh")
    ud_merit.hover_template = l  
        
    print("mo_df.head()")
    mo_df = mo_df.to_dict('records')
    mo = mo.to_dict('records')
    dd_merit['color'] = "#EC9302"
    ud_merit['color'] = "#356CA5"
    dd_merit = dd_merit.to_dict('records')
    ud_merit = ud_merit.to_dict('records')
    mo_final = mo_final.to_dict('records')
    sum_amount_with_strategy  = rd_dem * ud_price -  rd_dem * dd_price
    
    return mo_final, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price, sum_amount_with_strategy


# callback for strategies
@callback(
    Output(component_id='bar-chart-2', component_property='figure'),
    Output(component_id='ud_demand-2', component_property='children'),
    Output(component_id='dd_demand-2', component_property='children'),
    Output(component_id='payoff_table-2', component_property='data'),
    Output(component_id='payoff_table_history-2', component_property='data'),
    Output(component_id='cap_constr-2', component_property='children'),
    Output(component_id='strategy-text-box-2', component_property='children'),
    Output(component_id='text-box-2', component_property='children'),
    Output(component_id='display-box-2', component_property='style'),
    Output(component_id='img-2', component_property='style'),
    Output(component_id='sanction-output-2',  component_property='children'),
    Output(component_id='text-summary-2',  component_property='children'),



    Input(component_id='generator_select-2', component_property='value'),
    Input(component_id='strategy-2', component_property='value'),
    Input(component_id='load_input-2', component_property='value'),
    Input(component_id='mo_df_hold-2', component_property='data'),
    Input(component_id='mo_hold-2', component_property='data'),
    Input(component_id='dd_merit_hold-2', component_property='data'),
    Input(component_id='ud_merit_hold-2', component_property='data'),
    Input(component_id='rd_dem_hold-2', component_property='value'),
    Input(component_id='clearing_price_hold-2', component_property='value'),
    Input(component_id='capacity_input-2', component_property='value'),
    Input(component_id='Anticipation-switch-2', component_property='value'),
    Input(component_id='sum-amount-2', component_property='value'),
    Input(component_id='sanction-input-2', component_property='value'),
    Input(component_id='redispatch-pricing-2', component_property='value'),
    Input('save-payoff-2', 'n_clicks'),

)
def strategies_select(load_sel, strategy, capacity_mw, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price, power_mw, anticipation,sum_amount_without_strategy,sanction,redispatch_pricing,n_clicks):
    
    global counter
    counter = counter
    fig,  print_ud, print_dd, payoff_table, payoff_export_dataframe,cap_cons, strategy_box_text,text_box ,style,style_1,sanction_output,counter,text_summary  = strategies_sel(load_sel, strategy, capacity_mw, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price, power_mw,sum_amount_without_strategy, sanction, n_clicks, counter,anticipation,type = 'load', redispatch_pricing=redispatch_pricing)
    return fig,  print_ud, print_dd, payoff_table,payoff_export_dataframe, cap_cons, strategy_box_text,text_box,style,style_1, sanction_output,text_summary


# callback for select button
@callback(
    Output(component_id='generator_select-2', component_property='options'),
    Input(component_id='new_table-2', component_property='data'),
    Input(component_id='strategy-2', component_property='value'),)
def add_select_options(data,strategy_sel):
    data = pd.DataFrame(data)
    if data.empty:
        data = pd.DataFrame(columns=['Name'])
    dict_select = [{'label': 'None', 'value': None}] + \
        [{'label': i, 'value': i.split('(')[0]} for i in data.Name.tolist()]
    return dict_select


# callback to edit table at node 1
@callback(
    Output('node1_table-2', 'data'),
    Input('add_row_node1-2', 'n_clicks'),
    State('node1_table-2', 'data'),
    State('node1_table-2', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

# callback to edit table at node 2


@callback(
    Output('node2_table-2', 'data'),
    Input('add_row_node2-2', 'n_clicks'),
    State('node2_table-2', 'data'),
    State('node2_table-2', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows
