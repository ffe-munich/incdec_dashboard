from matplotlib.pyplot import figimage
import pandas as pd
import numpy as np
import os
import math
from utils.plot import plot_function
from utils.functions import payoffs


def pthresh_rate(p_thresh):
    
    if p_thresh <= 0 :
        p_thresh = 0.0
    elif p_thresh >= 1 :
        p_thresh = 100
    else:
        p_thresh = p_thresh  * 100
    
    return p_thresh

def strategies_sel(sel, strategy, mw_1, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price, mw_2,sum_amount_without_strategy,sanction, anticipation,type = 'gen',redispatch_pricing = 'uniform price'):
    try:
        sel = sel.split("(")[0]
    except:
        sel = sel
    fig_plot = ""    
    if anticipation != 'No Anticipation':
        
        on = True
    else:
        on = False
     
    
    mo_df = pd.DataFrame(mo_df)
    mo = pd.DataFrame(mo)
    dd_merit = pd.DataFrame(dd_merit)
    ud_merit = pd.DataFrame(ud_merit)
    
    rd_dem_dd= rd_dem
    rd_dem_ud = rd_dem
  
    board = type

    if type == 'load': 
        capacity_mw = mw_1
        load_mw = mw_2
        mul = mo_df['bid'] * mo_df['disp']
        spot = mul.sum()
        
        dd_price = dd_merit.red_bid[dd_merit.rd != 0].max()
        ud_price = ud_merit.red_bid[ud_merit.rd != 0].min()
        mo_df.rename(columns = {'Name':'name'}, inplace = True)
        mo.rename(columns = {'Name':'name'}, inplace = True)
        dd_merit.rename(columns = {'Name':'name'}, inplace = True)
        ud_merit.rename(columns = {'Name':'name'}, inplace = True)
        mo_df['Name'],mo['Name'],dd_merit['Name'],ud_merit['Name'] = mo_df['name'], mo['name'], dd_merit['name'], ud_merit['name']    
            
    else:
        
        load_mw = mw_1
        capacity_mw = mw_2
        mul = mo_df['bid'] * mo_df['disp']
        spot = mul.sum()
        ud_price = ud_merit.red_bid[ud_merit.rd!=0].max()
        dd_price = dd_merit.red_bid[dd_merit.rd!=0].min()
        
    
    if strategy == 'Stochastic Non-Attribution' and on:
  
        if sel in dd_merit['name'].tolist():
            dd_merit['new_rd'] = 0.0 
            
            rd_remove = dd_merit[dd_merit.name == sel].rd
            rd_remove = rd_remove.values
            
            row_sel = dd_merit[dd_merit.name == sel]
            dd_merit = dd_merit[dd_merit.name != sel]
            x = row_sel.cap if type == 'gen' else row_sel.Load
            rd_dem_dd = rd_dem + int(x)
            
            for idx,row in dd_merit.iterrows():
                
                if row.disp != 0:
                    if -1*rd_remove >= (row.disp + row.rd) :
                        dd_merit.loc[idx,'new_rd'] = -1*row.disp
                        
                        rd_remove = rd_remove + row.disp + row.rd
                        
                    else:
                       
                        dd_merit.loc[idx,'new_rd'] = rd_remove + row.rd
                        rd_remove = 0
            if rd_remove!=0:
                error_message = "Not sufficient assets for redispatch available"
                    
            dd_merit = pd.concat([dd_merit, row_sel])
            
            if type == 'gen':
                dd_merit = dd_merit.sort_values(by='name')
                dd_merit = dd_merit.sort_values(by='red_bid', ascending=False)
            
            else:
                dd_merit = dd_merit.sort_values(by='name', ascending=False)
                dd_merit = dd_merit.sort_values(by='red_bid')
            
                        
            dd_merit['rd'] = dd_merit['new_rd']    
            ud_merit['new_rd'] = ud_merit['rd']
            
               
        elif sel in ud_merit['name'].tolist():
            
            ud_merit['new_rd'] = 0.0 
            rd_add = ud_merit[ud_merit.name == sel].rd
            rd_add = rd_add.values
            
            row_sel = ud_merit[ud_merit.name == sel]
            ud_merit = ud_merit[ud_merit.name != sel]
            x = row_sel.cap if type == 'gen' else row_sel.Load
            rd_dem_ud = rd_dem + int(x)
            
            for idx,row in ud_merit.iterrows():
                x = row.cap if type == 'gen' else row.Load
                if rd_add >= (x - row.rd) :
                    
                    ud_merit.loc[idx,'new_rd'] = x    
                    rd_add = rd_add + row.rd - x
                        
                else:
                    ud_merit.loc[idx,'new_rd'] = rd_add + row.rd
                    rd_add = 0
                
            if rd_add!=0:
                error_message = "Not sufficient assets for redispatch available" 
            ud_merit = pd.concat([ud_merit, row_sel])
            
            if type == 'gen':
                ud_merit = ud_merit.sort_values(by='name')
                ud_merit = ud_merit.sort_values(by='red_bid', ascending=True)
            
            else:
                ud_merit = ud_merit.sort_values(by='name', ascending=False)
                ud_merit = ud_merit.sort_values(by='red_bid', ascending=False)
                
            
            
            ud_merit['rd'] = ud_merit['new_rd'] 
            dd_merit['new_rd'] = dd_merit['rd']
             
        else:
            ud_merit['new_rd'] = ud_merit['rd']
            dd_merit['new_rd'] = dd_merit['rd']   
        
        mo_new_rd = pd.concat([dd_merit,ud_merit],axis = 0)
        mo_new_rd = mo_new_rd[['name','new_rd']]
        mo_df = pd.merge(mo_df,mo_new_rd,on='name',how='right')
        mo_df['rd'] = mo_df['new_rd']
        mo_df.drop(['new_rd'], axis = 1, inplace=True)
        
        if type == 'gen':
            ud_price = ud_merit.red_bid[ud_merit.new_rd!=0].max()
            dd_price = dd_merit.red_bid[dd_merit.new_rd!=0].min()
            mo_df.sort_values(by='bid', ascending=True, inplace= True)
            mo_df['prod'] = mo_df.disp + mo_df.rd
        
        else:
            ud_price = ud_merit.red_bid[ud_merit.new_rd != 0].min()
            dd_price = dd_merit.red_bid[dd_merit.new_rd != 0].max()
            mo_df.sort_values(by='bid', inplace=True, ascending=False)
            mo_df['power_receive'] = mo_df.disp + mo_df.rd
            mo_df['x_pos'] = mo_df.Load.cumsum() - 0.5*mo_df.Load
        
        mo_df['payoff_anticipated_strategy'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = board,redispatch_pricing=redispatch_pricing,sel = None,capacity_pricing = False),axis=1)
        
        if sel in dd_merit['name'].tolist():
            row_sel = mo_df[mo_df.name == sel]
          
            name,payoff_anticipated_strategy, payoff_anticipated,payoff_without_anticipated, = row_sel['name'].tolist()[0], row_sel['payoff_anticipated_strategy'].tolist()[0], row_sel['payoff_anticipated'].tolist()[0], \
                                                                                              row_sel['payoff_without_anticipated'].tolist()[0]
                                                                                              
            if type == 'gen':                                                                                  
                prod, cost    = row_sel['prod'].tolist()[0], row_sel['cost'].tolist()[0]                                                                               
                dd_merit.loc[dd_merit['name'] == sel, 'color'] = '#7198c0'
                dd_price=dd_merit.red_bid[dd_merit.rd!=0].min()
                
            else:
                power_receive, WTP = row_sel['power_receive'].tolist()[0], row_sel['WTP'].tolist()[0]
                dd_merit.loc[dd_merit['Name'] == sel, 'color'] = '#f3be67'
                dd_price = dd_merit.red_bid[dd_merit.rd != 0].max()
            
            try:
                p_thresh =  round((payoff_without_anticipated - payoff_anticipated)/(payoff_anticipated_strategy - payoff_anticipated),2)
            except:
                p_thresh = 0
            p_thresh =  pthresh_rate(p_thresh)

            sum_amount = rd_dem * ud_price -  rd_dem * dd_price  if type == 'gen' else rd_dem * dd_price - rd_dem * ud_price
            
        
            if redispatch_pricing == "pay-as-bid":
                sum_amount  = (mo_df['rd']* mo_df['red_bid']).sum()
            if type == 'load' and redispatch_pricing == 'pay-as-bid':
                sum_amount = sum_amount * -1
            if type =='load':
                total_redispatch_cost = sum_amount + sum_amount_without_strategy
                
            else:
                total_redispatch_cost = sum_amount - sum_amount_without_strategy
                
            
            
            
        elif sel in ud_merit['name'].tolist():
            
            row_sel = mo_df[mo_df.name ==sel]
            
            if type == 'gen':
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#f3be67' 
                ud_price = ud_merit.red_bid[ud_merit.rd!=0].max()
                
            else:
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#7198c0'
                ud_price = ud_merit.red_bid[ud_merit.rd != 0].min()
                
            name,payoff_anticipated_strategy, payoff_anticipated,payoff_without_anticipated, bid = row_sel['name'].tolist()[0], row_sel['payoff_anticipated_strategy'].tolist()[0], row_sel['payoff_anticipated'].tolist()[0], \
                                                                                             row_sel['payoff_without_anticipated'].tolist()[0], row_sel['bid'].tolist()[0]
                                                        
            try:
                p_thresh =  round((payoff_without_anticipated - payoff_anticipated)/(payoff_anticipated_strategy - payoff_anticipated),2)
                p_thresh =  pthresh_rate(p_thresh)
            except:
                p_thresh = 0
            
            
            sum_amount = rd_dem * ud_price -  rd_dem * dd_price if type == 'gen' else rd_dem * dd_price - rd_dem * ud_price
            if redispatch_pricing == "pay-as-bid":
                sum_amount  = (mo_df['rd']* mo_df['red_bid']).sum()
            if type == 'load' and redispatch_pricing == 'pay-as-bid':
                sum_amount = sum_amount * -1    
            if type == 'gen':    
                total_redispatch_cost = sum_amount - sum_amount_without_strategy  
            else:
                total_redispatch_cost = sum_amount + sum_amount_without_strategy  
                              
           
       
            
    elif strategy == "Monitoring and Penalization" and on:
        
        df = mo_df[mo_df.name == sel]
        if not df.empty:

            prob = 0.01
            
            if type == 'gen':  
                dev = abs(df.cost - df.bid)
                det_prob = prob * dev
                deduct_payoff = sanction * det_prob
                deduct_payoff = round(deduct_payoff.values[0],2)
                if deduct_payoff % 1 == 0 or round(deduct_payoff % 1,2) == .99 or round(deduct_payoff % 1,2) == .01:
                    deduct_payoff = round(deduct_payoff)
                
                s_thres = (df.payoff_anticipated - df.payoff_without_anticipated ) /det_prob 
                
                mo_df.loc[mo_df['name'] == sel, 'payoff_anticipated'] = df.payoff_anticipated - deduct_payoff
                
                df = mo_df[mo_df.name == sel]
              
                
                
            else:
                dev = abs(df.WTP - df.bid)
                det_prob = prob * dev
                deduct_payoff = sanction * det_prob
                deduct_payoff = round(deduct_payoff.values[0],2)
                if deduct_payoff % 1 == 0 or round(deduct_payoff % 1,2) == .99 or round(deduct_payoff % 1,2) == .01:
                    deduct_payoff = round(deduct_payoff)
                
                s_thres = (df.payoff_anticipated - df.payoff_without_anticipated ) /det_prob 
                
                mo_df.loc[mo_df['name'] == sel, 'payoff_anticipated'] = df.payoff_anticipated - deduct_payoff
                
                df = mo_df[mo_df.name == sel]
                x= 'detected'  
                                
              
        
    
    elif strategy == "Capacity Pricing" and on:
        
        
        if sel in dd_merit['name'].tolist():
            dd_merit.loc[dd_merit['name'] == sel, 'red_bid'] = clearing_price 
           
                    
            print(f"sel: {sel} clearing price: {clearing_price}")
            if type == 'gen':
                dd_merit.loc[dd_merit['name'] == sel, 'real_cost'] = clearing_price
                dd_merit = dd_merit.sort_values(by='name')
                dd_merit = dd_merit.sort_values(by='red_bid', ascending=False)
            
            else:
                print(dd_merit['name'] == sel)
                dd_merit.loc[dd_merit['name'] == sel, 'real_WTP'] = clearing_price
                dd_merit = dd_merit.sort_values(by='name', ascending=False)
                dd_merit = dd_merit.sort_values(by='red_bid')  
         
           
        elif sel in ud_merit['name'].tolist():
            ud_merit.loc[ud_merit['name'] == sel, 'red_bid'] = clearing_price
            
           
            print(f"sel: {sel} clearing price: {clearing_price}")
            if type == 'gen':
                ud_merit.loc[ud_merit['name'] == sel, 'real_cost'] = clearing_price
                ud_merit = ud_merit.sort_values(by='name')
                ud_merit = ud_merit.sort_values(by='red_bid', ascending=True)
            
            else:
                ud_merit.loc[ud_merit['name'] == sel, 'real_WTP'] = clearing_price
                ud_merit = ud_merit.sort_values(by='name', ascending=False)
                ud_merit = ud_merit.sort_values(by='red_bid', ascending=False)
                
        
        if type == 'gen':
            ud_price = ud_merit.red_bid[ud_merit.rd != 0].max()
            dd_price = dd_merit.red_bid[dd_merit.rd != 0].min()
            mo_df.sort_values(by='bid', ascending=True, inplace= True)
            mo_df['prod'] = mo_df.disp + mo_df.rd
            mo_df.loc[mo_df['name'] == sel, 'real_cost'] = clearing_price
        
        else:
            ud_price = ud_merit.red_bid[ud_merit.rd != 0].min()
            dd_price = dd_merit.red_bid[dd_merit.rd != 0].max()
            mo_df.sort_values(by='bid', inplace=True, ascending=False)
            mo_df['power_receive'] = mo_df.disp + mo_df.rd
            mo_df['x_pos'] = mo_df.Load.cumsum() - 0.5*mo_df.Load
            mo_df.loc[mo_df['name'] == sel, 'real_WTP'] = clearing_price
        
        mo_df['payoff_anticipated_strategy'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = board,redispatch_pricing=redispatch_pricing,sel = sel,capacity_pricing = True ),axis=1)
        # print(mo_df.head())
        if sel in dd_merit['name'].tolist():
            
                                                                                              
            if type == 'gen':                                                                                  
                                                                                              
                dd_merit.loc[dd_merit['name'] == sel, 'color'] = '#7198c0'
                dd_price=dd_merit.red_bid[dd_merit.rd!=0].min()
                
            else:
                
                dd_merit.loc[dd_merit['Name'] == sel, 'color'] = '#f3be67'
                dd_price = dd_merit.red_bid[dd_merit.rd != 0].max()
 
            
            
        elif sel in ud_merit['name'].tolist():
            
            
            if type == 'gen':
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#f3be67' 
                ud_price = ud_merit.red_bid[ud_merit.rd!=0].max()
                
            else:
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#7198c0'
                ud_price = ud_merit.red_bid[ud_merit.rd != 0].min()
             
                              
           

    else:
        t = 1    
    if type == 'gen':           
        conditions = [(mo_df['bid']!= mo_df['cost']) & (mo_df['node'] == 1), (mo_df['bid']!= mo_df['cost']) & (mo_df['node'] == 2) , mo_df['bid']== mo_df['cost']]
        # width, y, meta = format(width,'.2f'), format(y,'.2f'), format(meta,'.2f') 
        
        mo_df['x_pos'] = mo_df.cap.cumsum() - 0.5*mo_df.cap
        
    else:
        conditions = [(mo_df['bid'] != mo_df['WTP']) & (mo_df['Node'] == 1), (mo_df['bid']
                                                                          != mo_df['WTP']) & (mo_df['Node'] == 2), mo_df['bid'] == mo_df['WTP']]
      
        mo_df['x_pos'] = mo_df.Load.cumsum() - 0.5*mo_df.Load
        

    mo_df.set_index(["name"],inplace=True)
    mo.set_index(["name"],inplace=True)
    dd_merit.set_index(["name"],inplace=True)
    ud_merit.set_index(["name"],inplace=True)
        
    if on and ('payoff_anticipated_strategy' in mo_df.columns):
        mo_df['payoff'] = mo_df['payoff_anticipated_strategy']
    
    elif on:
        mo_df['payoff'] = mo_df['payoff_anticipated']
        
    else:
        mo_df['payoff'] = mo_df['payoff_without_anticipated']  
        
    sum_amount = rd_dem * ud_price -  rd_dem * dd_price if type == 'gen' else rd_dem * dd_price - rd_dem * ud_price
   
    if redispatch_pricing == "pay-as-bid":
        sum_amount  = (mo_df['rd']* mo_df['red_bid']).sum() if type == 'gen' else (mo_df['rd']* mo_df['red_bid']).sum() 
        if type == 'load':
            sum_amount = -1 * sum_amount
    if  math.isnan(sum_amount):
        spot = spot 
    else:       
        spot = spot + sum_amount
    spot =  round(spot) if format(spot,'.2f')[-2:] == '00' else format(spot,'.2f')
    sum_amount = round(sum_amount) if format(sum_amount,'.2f')[-2:] == '00' else format(sum_amount,'.2f')
    if on:
        val = True
    else:
        val = False
    
    
    if sum_amount == 'nan':
                sum_amount = 0
    
        
    rd_dem = format(rd_dem, '.2f')
    line_flow_end = 0
    if type == 'gen':
        line_flow_end = mo_df[mo_df.node == 1]['prod'].sum()
    else:
        line_flow_end = mo_df[mo_df.Node == 2]['power_receive'].sum()
              
    mo_df = mo_df.reset_index()  
    mo_df['payoff'] = mo_df['payoff'].map('{:,.2f}€'.format)
    
    payoff_table =  mo_df[['name','payoff']].sort_values(by = 'name')
    payoff_table = payoff_table.set_index('name').transpose()
    
    return payoff_table