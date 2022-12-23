from re import M
import math
import pandas as pd
import numpy as np
from dash import dash_table
from sqlalchemy import true
from utils.plot import plot_function

def redispatch(mo,load,line_cap,anticipation ='No Anticipation',pay_as_bid= "uniform pricing",freeze_bool = 'False'):
    '''
    

    Parameters
    ----------
    mo : dataframe
        merit order of bids at both nodes.
    load : numeric
        load in MW at node 2.
    line_cap : numeric
        line capacity in MW between node 1 and node 2.

    Returns
    -------
    None.

    '''
    
    if freeze_bool == 'False':
    # initialize dispatch and redispatch columns
        
        mo['disp']=np.nan
        mo['rd']=np.nan
        mo['hover_template'] = '<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh'
        # calculate dispatch individual amounts
        rem_load = load
        for idx, row in mo.iterrows():
            if rem_load >= row.cap:
                mo.loc[idx,'disp'] = row.cap
                rem_load -= row.cap
            else:
                mo.loc[idx,'disp'] = rem_load
                rem_load = 0
                
        # calculate redispatch demand from dispatch and line capacity
        rd_dem = max(mo.disp[mo.node==1].sum()-line_cap,0)
            
        
        
        mo['hover_template'] = '<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh'
        # divide df into updispatch and downdispatch side
        mo_1 = mo[mo.node==1]
        mo_2 = mo[mo.node==2]
        
        
        mo_1['red_bid'] = mo_1.cost.copy()
        mo_2['red_bid'] = mo_2.cost.copy()
       
        mo_1.sort_values(by='red_bid',ascending=False,inplace = True)
        mo_2.sort_values(by='red_bid',ascending=True, inplace =True)
        
        dd_sum = rd_dem
        
        for idx, row in mo_1.iterrows():   
            if dd_sum >= row.disp:
                mo_1.loc[idx,'rd'] = -1*row.disp
                dd_sum -= row.disp
            else:
                mo_1.loc[idx,'rd'] = -1*dd_sum
                dd_sum = 0
                
        # price for downdispatch
        dd_price=mo_1.red_bid[mo_1.rd!=0].min()
    
        if anticipation == 'Full Anticipation':
    
            if mo.mark.sum() == 0:
                mo_1.loc[mo_1['bid']>dd_price,'bid'] = dd_price
        # calculate individual updispatch 
        ud_sum = rd_dem
        for idx, row in mo_2.iterrows():   
            if ud_sum >= row.cap-row.disp:
                mo_2.loc[idx,'rd'] = row.cap-row.disp
                ud_sum -= row.cap-row.disp
            else:
                mo_2.loc[idx,'rd'] = ud_sum
                ud_sum = 0
            
    # price for updispatch
        ud_price = mo_2.red_bid[mo_2.rd!=0].max()
        
        
        if pay_as_bid == 'pay-as-bid':
        
        
            name_mo_1 = mo_1[mo_1.rd == 0.0].index
            name_mo_2 = mo_2[mo_2.rd == 0.0].index
            red_1 = mo_1.loc[name_mo_1] 
            red_2 = mo_2.loc[name_mo_2] 
            
            mo_1.red_bid= mo_1.cost + 0.7 * (dd_price - mo_1.cost)
            mo_2.red_bid = mo_2.cost + 0.7 * (ud_price - mo_2.cost)
            mo_1.loc[name_mo_1] = red_1
            mo_2.loc[name_mo_2] = red_2
            
            mo_1.loc[mo_1['bid']<mo_1['red_bid'],'bid'] = mo_1.red_bid
            mo_2.loc[mo_2['bid']>mo_2['red_bid'],'bid'] = mo_2.red_bid
            l =[]
            mo_1.reset_index(inplace = True)
            for i in mo_1.iterrows():
                if i[1]['red_bid'] != i[1]['cost']:
                    s = str(i[1]['name']) + " bids " + str(i[1]['red_bid']) + " €/MWh at the redispatch market instead of their marginal cost of " + str(i[1]['cost']) + " €/MWh adjusting their <br> bid towards the anticipated market clearing price to maximize their payoff."
                    l.append(s)
                else:
                    l.append("<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh")
            mo_1.set_index('name',inplace = True)
            mo_1['hover_template'] = l
            l = []
            mo_2.reset_index(inplace = True)
            for i in mo_2.iterrows():
                if i[1]['red_bid'] != i[1]['cost']:
                    s = str(i[1]['name']) + " bids " + str(i[1]['red_bid']) + " €/MWh at the redispatch market instead of their marginal cost of " + str(i[1]['cost']) + " €/MWh adjusting <br> their bid towards the anticipated market clearing price to maximize their payoff."
                    l.append(s)
                else:
                    l.append("<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh")
            mo_2.set_index('name',inplace = True)
            mo_2['hover_template'] = l
            
        
        
    return(mo_1,mo_2,rd_dem,dd_price,ud_price)
    

def redispatch_load(mo,power,line_cap, pay_as_bid= "uniform pricing",freeze_bool = 'False'):
    '''
    

    Parameters
    ----------
    mo : dataframe
        merit order of bids at both nodes.
    load : numeric
        load in MW at node 2.
    line_cap : numeric
        line capacity in MW between node 1 and node 2.

    Returns
    -------
    None.

    '''
    # initialize dispatch and redispatch columns
    if freeze_bool == 'False':
        mo['disp']=np.nan
        mo['rd']=np.nan
        mo['hover_template'] = '<b>%{width}</b> MW at <br><b>%{y}</b> €/MWh'
        # calculate dispatch individual amounts
        rem_load = power
        for idx, row in mo.iterrows():
            if rem_load >= row.Load:
                mo.loc[idx,'disp'] = row.Load
                rem_load -= row.Load
            else:
                mo.loc[idx,'disp'] = rem_load
                rem_load = 0
                
        # calculate redispatch demand from dispatch and line capacity
        rd_dem = max(mo.disp[mo.Node==2].sum()-line_cap,0)
        
        # divide df into updispatch and downdispatch side
        mo_2 = mo[mo.Node==2].sort_values(by='bid')
        mo_1 = mo[mo.Node==1]
        mo_1['red_bid']= mo_1.WTP.copy()
        mo_2['red_bid'] = mo_2.WTP.copy()
        mo_1.sort_values(by='red_bid',ascending=False,inplace = True)
        mo_2.sort_values(by='red_bid',ascending=True, inplace =True)
        # calculate individual downdispatch
        dd_sum = rd_dem
        for idx, row in mo_2.iterrows():   
            if dd_sum >= row.disp:
                mo_2.loc[idx,'rd'] = -1*row.disp
                dd_sum -= row.disp
            else:
                mo_2.loc[idx,'rd'] = -1*dd_sum
                dd_sum = 0
                
        # price for downdispatch
        dd_price=mo_2.red_bid[mo_2.rd!=0].max()
        # if anticipation == 'Full Anticipation':
        #     print("inside: ", dd_price)
        #     mo_1.loc[mo_2['bid']>dd_price,'bid'] = dd_price
        # calculate individual updispatch 
        ud_sum = rd_dem
        for idx, row in mo_1.iterrows():   
            if ud_sum >= row.Load-row.disp:
                mo_1.loc[idx,'rd'] = row.Load-row.disp
                ud_sum -= row.Load-row.disp
            else:
                mo_1.loc[idx,'rd'] = ud_sum
                ud_sum = 0
    
        mo_2['pay_as_bid_red'] = mo_2['red_bid']
        mo_1['pay_as_bid_red'] = mo_1['red_bid']
        ud_price = mo_1.red_bid[mo_1.rd!=0].min()
        name_mo_1 = mo_1[mo_1.rd == 0.0].index
        name_mo_2 = mo_2[mo_2.rd == 0.0].index
        red_1 = mo_1.loc[name_mo_1] 
        red_2 = mo_2.loc[name_mo_2] 
        # print(red_1)
        # print(mo_2.WTP + 0.7 * (dd_price - mo_2.WTP))
        mo_2.pay_as_bid_red = mo_2.WTP + 0.7 * (dd_price - mo_2.WTP)
        mo_1.pay_as_bid_red = mo_1.WTP + 0.7 * (ud_price - mo_1.WTP)
        
        mo_1.loc[name_mo_1] = red_1
        mo_2.loc[name_mo_2] = red_2
        mo_1.loc[mo_1['bid']>mo_1['red_bid'],'bid'] = mo_1.red_bid
        mo_2.loc[mo_2['bid']<mo_2['red_bid'],'bid'] = mo_2.red_bid
        
        
        

        
    return(mo_1,mo_2,rd_dem,dd_price,ud_price)



def payoffs(x, cp, udp, ddp , type = 'gen', redispatch_pricing = 'uniform pricing'):
    '''
    calculates payoffs 
    
    Parameters
    ----------
    x : dataframe
        DESCRIPTION.
    cp : numeric
        spot market clearing price.
    udp : numeric
        updispatch clearing price.
    ddp : numeric
        updispatch clearing price.

    Returns
    -------
    y : numeric
        resulting payoff for individual agent.

    '''
    # print(x)
    if x.rd < 0 and type == 'gen' and redispatch_pricing == 'uniform pricing':
        y = x.disp * cp + x.rd*ddp - x['prod']*x.real_cost  
    elif x.rd < 0 and type == 'gen' and redispatch_pricing == 'pay-as-bid':
        y = x.disp * cp + x.rd*x.red_bid - x['prod']*x.real_cost  
        
    elif x.rd < 0 and type == 'load' and redispatch_pricing == 'uniform pricing':
        y = -x.disp *cp - x.rd*ddp + x['power_receive'] * x.real_WTP
    
    elif x.rd < 0 and type == 'load' and redispatch_pricing == 'pay-as-bid':
        y = x.disp * cp - x.rd*x.red_bid + x['power_receive']*x.real_WTP  
        
    
    elif x.rd == 0 and type == 'gen':
        y = x.disp * cp - x['prod']*x.real_cost  
        
    elif x.rd == 0 and type == 'load':
        y = - x.disp *cp + x['power_receive'] * x.real_WTP
                
        
    elif type == 'gen' and redispatch_pricing == 'uniform pricing':
        y = x.disp * cp + x.rd*udp - x['prod']*x.real_cost
           
    elif type == 'gen' and redispatch_pricing == 'pay-as-bid':
        y = x.disp * cp + x.rd*x.red_bid - x['prod']*x.real_cost
        
    elif type == 'load' and redispatch_pricing == 'uniform pricing':
        y = -x.disp * cp - x.rd*udp + x['power_receive']*x.real_WTP  
            
    else: 
        y = -x.disp * cp - x.rd*x.red_bid + x['power_receive']*x.real_WTP  
        
    return round(y,2)
    
    
def game(x,mo_left_for_disp,mo_left_for_down_disp,max_node_1_cost,min_node_2_cost,line_capacity, udp, ddp,production_line_flow, markup, x_max, x_min, type = 'gen', strat = 'Full Anticipation',redispatch_pricing='uniform-pricing'):
    '''
    calculate strategic bids

    Parameters
    ----------
    x : dataframe
        DESCRIPTION.
    udp : numeric
        updispatch clearing price.
    ddp : numeric
        downdispatch clearing price.
    markup : numeric
        price markup to set bids above marginal costs

    Returns
    -------
    y : TYPE
        DESCRIPTION.

    '''
    def normalize (x, x_min=x_min, x_max=x_max):
        x_norm = (x-x_min)/(x_max-x_min)
        return x_norm
    
    if strat == 'Full Anticipation':
        
        mark = 0
        if type == 'gen':
            p = x.cost  
            l = x.cost
        else:
            p = x.WTP  
            l = x.WTP
        if (x.Game == True or x.Game =='true') and (not np.isnan(udp)) and type == 'gen':
            x_total = x.cost+markup
            
            if x.node == 2:
                if x_total != udp: 
                    y = max(udp - 0.001, x_total)
                else:
                    y = x_total
            elif x.node == 1:
                if x_total != ddp: 
                    y = min(ddp + 0.001, x_total) 
                
                else:
                    y = x_total
                
        elif (x.Game == True or x.Game =='true' or x.Game != 'false') and (not np.isnan(udp)) and type == 'load':
            print(x.Game)
            x_total = x.WTP+markup
            
            if x.Node == 2:
                if x_total != ddp:  
                    y = max(ddp - 0.001, x_total)
                else:
                    y = x_total
            elif x.Node == 1:
                if x_total != udp:  
                    y = min(udp - 0.001, x_total)
                else:
                    y = x_total
        else:
            if type == 'gen':
                y = x.cost       
            else:
                y = x.real_WTP
        if type == 'gen':        
            if math.isnan(udp):
                
                count = 0
                cond = False
                l =x.cost
                if x.node ==2 and  x.disp != 0:
                    tmp = x.cap
                    for idx, row in mo_left_for_disp.iterrows():
                        tmp = tmp- row.left_to_disp
                        count += 1
                        
                        if tmp <= 0:
                            mo_left_for_disp = mo_left_for_disp.head(count)
                            break
                    count = 0
                    sum_left_disp = mo_left_for_disp[mo_left_for_disp.node == 1]['left_to_disp'].sum() 
                    if sum_left_disp == 0:
                        cond = False
                    elif sum_left_disp >= x.cap and x.cap + production_line_flow > line_capacity:   
                        cond = True
                    elif sum_left_disp + production_line_flow > line_capacity:
                        cond = True                      
                        
                    if x.cost < min_node_2_cost and cond:
                        y = min_node_2_cost
                        l = min_node_2_cost
                        mark = 1
                        
                elif x.node == 1 and x.disp == 0:
                    tmp = x.cap
                    for idx, row in mo_left_for_down_disp.iterrows():
                        tmp = tmp- row.disp
                        count += 1
                        if tmp <= 0:
                            mo_left_for_down_disp =mo_left_for_down_disp.head(count)
                            break
                    sum_right_disp = mo_left_for_down_disp[mo_left_for_down_disp.node == 1]['disp'].sum() 
                   
                    
                    if sum_right_disp == 0 and x.cap + production_line_flow > line_capacity:
                        cond = True
    
                    else :
                        cond = False
                        
                    if x.cost > max_node_1_cost and cond:
                        y = max_node_1_cost + 0.001
                        l = max_node_1_cost +0.001 
                        mark = 1
        elif type == 'load':
            mo_left_to_receive = mo_left_for_disp
            mo_left_not_to_receive = mo_left_for_down_disp
            if math.isnan(udp):
            
                count = 0
                cond = False
                l =x.WTP
                if x.Node ==2 and  x.disp == 0:
                    tmp = x.Load
                    for idx, row in mo_left_not_to_receive.iterrows():
                        tmp = tmp- row.left_to_receive
                        count += 1
                        
                        if tmp <= 0:
                            mo_left_not_to_receive = mo_left_not_to_receive.head(count)
                            break
                    count = 0
                    sum_left_not_to_receive = mo_left_not_to_receive[mo_left_not_to_receive.Node == 1]['disp'].sum() 
                   
                   
                   
                    if sum_left_not_to_receive == 0:
                        cond = False
                    elif sum_left_not_to_receive >= x.Load and x.Load + production_line_flow > line_capacity:   
                        cond = True
                    elif sum_left_not_to_receive + production_line_flow > line_capacity:
                        cond = True                      
                        
                    if x.Load < min_node_2_cost and cond and x.Game == 'true':
                        y = min_node_2_cost-0.001
                        l = min_node_2_cost - 0.001
                        mark = 1
                        
                elif x.Node == 1 and x.disp != 0:
                    tmp = x.Load
                    
                    for idx, row in mo_left_to_receive.iterrows():
                        tmp = tmp- row.disp
                        count += 1
                        if tmp <= 0:
                            mo_left_to_receive = mo_left_to_receive.head(count)
                            break
                    sum_right_disp = mo_left_to_receive[mo_left_to_receive.Node == 2]['left_to_receive'].sum() 
                    
                    
                    
                    if sum_right_disp == 0:
                        cond = False
                    elif sum_right_disp >= x.disp and x.disp + production_line_flow > line_capacity: 
                        cond = True
                    elif sum_right_disp < x.disp and sum_right_disp + production_line_flow > line_capacity: 
                        cond = True
                    else :
                        cond = False
                        
                    if x.WTP > max_node_1_cost and cond and x.Game == 'true':
                        y = max_node_1_cost+0.001
                        l = max_node_1_cost+0.001
                        mark = 1
           
                      
                
 
    elif strat == 'Bayesian Equilibrium':  
        mark = 0
        if type == 'gen':
            p = x.cost  
            l = x.cost
        else:
            p = x.WTP  
            l = x.WTP
        if (x.Game == True or x.Game =='true') and (not np.isnan(udp)) and type == 'gen':
            x_total = x.cost+markup
            if x.node == 2:
                
                y = x_min + (x_max-x_min)*((1+normalize(x_total))/2)
            elif x.node == 1:
                y = x_min + (x_max-x_min)*(normalize(x_total)/2)
        elif (x.Game == True or x.Game =='true') and (not np.isnan(udp)) and type == 'load':
            x_total = x.WTP-markup
            
            if x.Node == 2:
                y = x_min + (x_max-x_min)*((1+normalize(x_total))/2)
            elif x.Node == 1:
                y = x_min + (x_max-x_min)*(normalize(x_total)/2)                
        else:
            if type == 'gen':
                y = x.cost       
            else:
                y = x.WTP
        
        
    return y,l,p,mark


def return_table(id_var,node =[],cols =[]):
    
    if id_var == 'payoff_table' or id_var == 'payoff_table-2' :
        table = dash_table.DataTable(
                               id=id_var,
                               editable=False,
                               row_deletable=False,
                            
                            #    css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
                               style_header={
                                            'backgroundColor': '#3D84BD',
                                             'fontWeight': 'bold',
                                             'color': 'white'
                                             },
                               style_cell={
                                            'backgroundColor': '#F2F2F2'
                                            },
            
                               
                               )
        
        
    elif  id_var == 'payoff_table_history' or id_var == 'payoff_table_history-2' :
        table = dash_table.DataTable(
                               id=id_var,
                               editable=False,
                               row_deletable=False,
                            
                            #    css=[{'selector': 'table', 'rule': 'table-layout: fixed'}],
                               style_header={
                                            'backgroundColor': '#3D84BD',
                                             'fontWeight': 'bold',
                                             'color': 'white'
                                             },
                               style_cell={
                                            'backgroundColor': '#F2F2F2'
                                            },
                               export_format="xlsx",
                               
                               )
               
    else:        
        table = dash_table.DataTable(data=node.to_dict('records'), 
                                columns=cols,
                                id=id_var,
                                editable=True,
                                row_deletable=True,
                                css=[{'selector': 'table', 'rule': 'table-layout: auto'}],
                                style_header={
                                                'backgroundColor': '#3D84BD',
                                                'fontWeight': 'bold',
                                                'color': 'white'
                                                },
                                style_cell={
                                                'backgroundColor': '#F2F2F2'
                                                },
                                )
    
    return table



