from cmath import nan
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

def strategies_sel(sel, strategy, mw_1, mo_df, mo, dd_merit, ud_merit, rd_dem, clearing_price, mw_2,sum_amount_without_strategy,sanction, n_clicks, counter, anticipation,type = 'gen',redispatch_pricing = 'uniform price'):
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
    strategy_box_text = " " 
    text_box = " "   
    sanction_output =" "
    error_message = " "
    board = type
    style = {'display': 'none'}
    style_1 = {'display': 'none', 'height':'60%', 'width':'85%'}
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
        
        mo_df['payoff_anticipated_strategy'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = board,redispatch_pricing=redispatch_pricing ),axis=1)
        
        if sel in dd_merit['name'].tolist():
            style_1 = {'display':'block','height':'40%', 'width':'65%','text-align':'center'}   
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
            print("payoff_without_anticipated: ",payoff_without_anticipated)  
            print("payoff_anticipated: ",payoff_anticipated) 
            print("payoff_anticipated_strategy: ",payoff_anticipated_strategy)  
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
                
            
            style_1 = {'display':'block','height':'40%', 'width':'65%','text-align':'center'}   
            
            if type == 'gen':
                strategy_box_text = f"Stochastistic non-attribution excludes {name} from downdispatch. Hence, they are forced to sell \
                                   {round(prod) if format(prod,'.2f')[-2:] == '00' else format(prod,'.2f')}\u00A0MWh at {round(clearing_price) if format(clearing_price,'.2f')[-2:] == '00' else format(clearing_price,'.2f')}\u00A0€/MWh despite their higher marginal costs of {round(cost) if format(cost,'.2f')[-2:] == '00' else format(cost,'.2f')}\u00A0€/MWh. \
                                    This results in a payoff of {round(payoff_anticipated_strategy) if format(payoff_anticipated_strategy,'.2f')[-2:] == '00' else format(payoff_anticipated_strategy,'.2f')}\u00A0€ compared to {round(payoff_anticipated) if format(payoff_anticipated,'.2f')[-2:] == '00' else format(payoff_anticipated,'.2f')}\u00A0€ when their strategic bidding was successful. \
                                    Thus, to have a sufficiently deterrent effect for generator {name}, the non-attribution rate (p) would need to be at least {round(p_thresh) if format(p_thresh,'.2f')[-2:] == '00' else format(p_thresh,'.2f')}%.\
                                    However, skipping {name} redispatch offer, the network operator accepts higher overall redispatch costs of {round(total_redispatch_cost) if format(total_redispatch_cost,'.2f')[-2:] == '00' else format(total_redispatch_cost,'.2f')}\u00A0€.   "
            else:
                strategy_box_text = f"Stochastistic non-attribution excludes {name} from downdispatch. Hence, they are forced to buy \
                                {round(power_receive) if format(power_receive,'.2f')[-2:] == '00' else format(power_receive,'.2f')}\u00A0MWh at {round(clearing_price) if format(clearing_price,'.2f')[-2:] == '00' else format(clearing_price,'.2f')}\u00A0€/MWh despite their lower willingness to pay of {round(WTP) if format(WTP,'.2f')[-2:] == '00' else format(WTP,'.2f')}\u00A0€/MWh. \
                                This results in a payoff of {round(payoff_anticipated_strategy) if format(payoff_anticipated_strategy,'.2f')[-2:] == '00' else format(payoff_anticipated_strategy,'.2f')}\u00A0€ compared to {round(payoff_anticipated) if format(payoff_anticipated,'.2f')[-2:] == '00' else format(payoff_anticipated,'.2f')}\u00A0€ when their strategic bidding was successful. \
                                Thus, to have a sufficiently deterrent effect for generator {name}, the non-attribution rate (p) would need to be at least {round(p_thresh) if format(p_thresh,'.2f')[-2:] == '00' else format(p_thresh,'.2f')}%.\
                                However, skipping {name} redispatch offer, the network operator accepts higher overall redispatch costs of {round(total_redispatch_cost) if format(total_redispatch_cost,'.2f')[-2:] == '00' else format(total_redispatch_cost,'.2f')}\u00A0€."
            
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
                              
            if type == 'gen':
                strategy_box_text = f"Stochastistic non-attribution excludes {name} from updispatch (provision of positive flexibility). Hence, with their bid of\
                                {round(bid) if format(bid,'.2f')[-2:] == '00' else format(bid,'.2f')}\u00A0€/MWh, they are not attributed in the spot market with a clearing price of  {round(clearing_price) if format(clearing_price,'.2f')[-2:] == '00' else format(clearing_price,'.2f')}\u00A0€/MWh and have to face foregone profits. \
                                This results in a payoff of {round(payoff_anticipated_strategy) if format(payoff_anticipated_strategy,'.2f')[-2:] == '00' else format(payoff_anticipated_strategy,'.2f')}\u00A0€ compared to {round(payoff_anticipated) if format(payoff_anticipated,'.2f')[-2:] == '00' else format(payoff_anticipated,'.2f')}\u00A0€ when their strategic bidding was successful. \
                                Thus, to have a sufficiently deterrent effect for generator {name}, the non-attribution rate (p) would need to be at least {round(p_thresh) if format(p_thresh,'.2f')[-2:] == '00' else format(p_thresh,'.2f')}%.\
                                However, skipping {name} redispatch offer, the network operator accepts higher overall redispatch costs of {round(total_redispatch_cost) if format(total_redispatch_cost,'.2f')[-2:] == '00' else format(total_redispatch_cost,'.2f')}\u00A0€."

            else:
                strategy_box_text = f"Stochastistic non-attribution excludes {name} from updispatch (provision of negative flexibility). Hence, they do not receive electricity with\
                                their bid of {round(bid) if format(bid,'.2f')[-2:] == '00' else format(bid,'.2f')}\u00A0€/MWh at the spot market with a clearing price of  {round(clearing_price) if format(clearing_price,'.2f')[-2:] == '00' else format(clearing_price,'.2f')}\u00A0€/MWh and have to face foregone utility from electricity consumption.\
                                This results in a payoff of {round(payoff_anticipated_strategy) if format(payoff_anticipated_strategy,'.2f')[-2:] == '00' else format(payoff_anticipated_strategy,'.2f')}\u00A0€ compared to {round(payoff_anticipated) if format(payoff_anticipated,'.2f')[-2:] == '00' else format(payoff_anticipated,'.2f')}\u00A0€ when their strategic bidding was successful. \
                                Thus, to have a sufficiently deterrent effect for load {name}, the non-attribution rate (p) would need to be at least {round(p_thresh) if format(p_thresh,'.2f')[-2:] == '00' else format(p_thresh,'.2f')}%.\
                                However, skipping {name} redispatch offer, the network operator accepts higher overall redispatch costs of {round(total_redispatch_cost) if format(total_redispatch_cost,'.2f')[-2:] == '00' else format(total_redispatch_cost,'.2f')}\u00A0€. "
            style_1 = {'display':'block','height':'40%', 'width':'65%','text-align':'center'}
            
        if os.path.exists("./payoff_export_dataframe.csv") and counter-n_clicks<=0:
            
            payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
            
            
            mo_df_dup = mo_df.reset_index()
            mo_df_dup = mo_df_dup.sort_values('name')
            l1 = mo_df_dup.name.tolist()
            l2 = mo_df_dup.payoff_anticipated_strategy.tolist()
            li = [None,None,None,None,None]  + [str(i)+"€"  for i in l2] + [None,None]
            
            payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
            
            payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)    
                 
            
    elif strategy == "Monitoring and Penalization" and on:
        
        df = mo_df[mo_df.name == sel]
        if not df.empty:
            style = {}
            prob = 0.01
            
            text_box = f"Monitoring aims at detecting strategic deviations of usual bidding behavior. The detection probability of strategic bidding increases with the absolute deviation compared to bids \
                in situations without congestion.  The detection probability per unit of bid deviation is defined as 'p'. Thus, the detection probability for a single actor is  defined as 'p*absolute(bid_game - bid_nogame)'. When strategic bidding is detected, the respective bidder has to pay a monetary sanction of 's'. For the detection probability per unit, we  assume 'p = 0.01'. To see the effect \
                of this mitigation strategy, enter a sanction here: " 
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
                x= 'detected'
                
                strategy_box_text = f"For Generator {df.name.values[0]}, their strategic bid deviation amounts to {round(dev.values[0],2)} €/MWh, so that their detection probability equals {round(det_prob.values[0],2):.2%} and their expected payoff is reduced by {round(deduct_payoff,2)}. \n \
                                    When bidding strategically, they have to expect a payoff of {df.payoff_anticipated.values[0]} € compared to {df.payoff_without_anticipated.values[0]} € when bidding truthfully. \n \
                                    Thus, to have a sufficiently deterrent effect for generator {df.name.values[0]}, the sanction would need to be at least {round(s_thres.values[0],2) }\u00A0€."
                
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
                                
                strategy_box_text = f"For Load {df.name.values[0]}, their strategic bid deviation amounts to {round(dev.values[0],2)} €/MWh, so that their detection probability equals {round(det_prob.values[0],2):.2%} and their expected payoff is reduced by {round(deduct_payoff,2)}. \n \
                                    When bidding strategically, they have to expect a payoff of {df.payoff_anticipated.values[0]} € compared to {df.payoff_without_anticipated.values[0]} € when bidding truthfully. \n \
                                    Thus, to have a sufficiently deterrent effect for load {df.name.values[0]}, the sanction would need to be at least {round(s_thres.values[0],2) }\u00A0€."
        
        
        if os.path.exists("./payoff_export_dataframe.csv") and counter-n_clicks<=0:
            
            payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
            
            mo_df_dup = mo_df.reset_index()
            mo_df_dup = mo_df_dup.sort_values('name')
            l1 = mo_df_dup.name.tolist()
            l2 = mo_df_dup.payoff_anticipated.tolist()
            li = [None,None,None,None,None] + [str(i)+"€"  for i in l2] + [None,None]
            
            payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
            
            payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
    
    elif strategy == "Capacity Pricing" and on:
        
        
        if sel in dd_merit['name'].tolist():
            dd_merit.loc[dd_merit['name'] == sel, 'red_bid'] = clearing_price 
            
                    
           
            if type == 'gen':
                dd_merit.loc[dd_merit['name'] == sel, 'real_cost'] = clearing_price
                dd_merit = dd_merit.sort_values(by='name')
                dd_merit = dd_merit.sort_values(by='red_bid', ascending=False)
            
            else:
                dd_merit.loc[dd_merit['name'] == sel, 'real_WTP'] = clearing_price
                dd_merit = dd_merit.sort_values(by='name', ascending=False)
                dd_merit = dd_merit.sort_values(by='red_bid')  
            
               
        elif sel in ud_merit['name'].tolist():
            ud_merit.loc[ud_merit['name'] == sel, 'red_bid'] = clearing_price
            
           
            
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
        
        mo_df['payoff_anticipated_strategy'] = mo_df.apply(lambda x: payoffs(x,cp=clearing_price,udp=ud_price,ddp=dd_price, type = board,redispatch_pricing=redispatch_pricing ),axis=1)
        
        if sel in dd_merit['name'].tolist():
            
                                                                                              
            if type == 'gen':                                                                                  
                                                                                              
                dd_merit.loc[dd_merit['name'] == sel, 'color'] = '#7198c0'
                rd_sum = sum(dd_merit['rd'].tolist())
                rd_sum = -1 * rd_sum
                for idx, row in dd_merit.iterrows():   
                    if rd_sum >= row.disp:
                        dd_merit.loc[idx,'rd'] = -1*row.disp
                        rd_sum -= row.disp
                    else:
                        dd_merit.loc[idx,'rd'] = -1*rd_sum
                        rd_sum = 0
                dd_price=dd_merit.red_bid[dd_merit.rd!=0].min()
                
                
            else:
                
                dd_merit.loc[dd_merit['Name'] == sel, 'color'] = '#f3be67'
                rd_sum = sum(dd_merit['rd'].tolist())
                rd_sum = -1 * rd_sum
                for idx, row in dd_merit.iterrows():   
                    if rd_sum >= row.disp:
                        dd_merit.loc[idx,'rd'] = -1*row.disp
                        rd_sum -= row.disp
                    else:
                        dd_merit.loc[idx,'rd'] = -1*rd_sum
                        rd_sum = 0
               
                dd_price = dd_merit.red_bid[dd_merit.rd != 0].max()
 
            
            if type == 'gen':
                strategy_box_text = f"With capacity pricing, instead of being able to buy back energy at the downdispatch price, {sel} commit themself to accept a cost neutral \
                    reversal of their spot market trade. As that alone may result in financial disadvantages, they are compensated additionally with periodical capacity market payments."
            else:
                strategy_box_text = f"With capacity pricing, instead of hoping for a high compensation payment for downdispatch, {sel} commit themself to accept a cost neutral reversal of \
                    their spot market trade. As that alone may result in financial disadvantages, they are compensated additionally with periodical capacity market payments."
            
        elif sel in ud_merit['name'].tolist():
            
            
            if type == 'gen':
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#f3be67' 
                rd_sum = sum(ud_merit['rd'].tolist())
                ud_merit['rd'] = 0
                for idx, row in ud_merit.iterrows():
                    if rd_sum >= row.cap:
                        ud_merit.loc[idx,'rd'] = row.cap
                        rd_sum -= row.cap
                    else:
                        ud_merit.loc[idx,'rd'] = rd_sum
                        rd_sum = 0
                ud_price = ud_merit.red_bid[ud_merit.rd!=0].max()
                
            else:
                ud_merit.loc[ud_merit['name'] == sel, 'color'] = '#7198c0'
                rd_sum = sum(ud_merit['rd'].tolist())
                
                ud_merit['rd'] = 0
                for idx, row in ud_merit.iterrows():
                    if rd_sum >= row.Load:
                        ud_merit.loc[idx,'rd'] = row.Load
                        rd_sum -= row.Load
                    else:
                        ud_merit.loc[idx,'rd'] = rd_sum
                        rd_sum = 0
                print(ud_merit.head())
                ud_price = ud_merit.red_bid[ud_merit.rd != 0].min()
             
                              
            if type == 'gen':
                strategy_box_text = f"With capacity pricing, instead of being awarded the updispatch price, {sel} commit themself to accept the spot market price for updispatch.\
                    As that alone may result in financial disadvantages, they are compensated additionally with periodical capacity market payments."
            else:
                strategy_box_text = f"With capacity pricing, instead of being awarded the updispatch price, {sel} commit themself to accept the spot market price for updispatch.\
                    As that alone may result in financial disadvantages, they are compensated additionally with periodical capacity market payments. "
           
            
        if os.path.exists("./payoff_export_dataframe.csv") and counter-n_clicks<=0:
            
            payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
            
            mo_df_dup = mo_df.reset_index()
            mo_df_dup = mo_df_dup.sort_values('name')
            l1 = mo_df_dup.name.tolist()
            l2 = mo_df_dup.payoff_anticipated_strategy.tolist()
            li = [None,None,None,None,None]  + [str(i)+"€"  for i in l2] + [None,None]
            
            payoff_export_dataframe.loc[len(payoff_export_dataframe)] = li
            
            payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
    else:
        t = 1    
    if type == 'gen':           
        conditions = [(mo_df['bid']!= mo_df['cost']) & (mo_df['node'] == 1), (mo_df['bid']!= mo_df['cost']) & (mo_df['node'] == 2) , mo_df['bid']== mo_df['cost']]
        # width, y, meta = format(width,'.2f'), format(y,'.2f'), format(meta,'.2f') 
        values = ['<b>%{text}</b> bids <b>%{width} MWh</b> on the spot market at <b>%{y} €/MWh</b><br> '
                'instead of their marginal cost of <b>%{meta} €/MWh</b> because they anticipate being <br>' 
                'able to buy back all the energy on the redispatch market for this price.', 
            
                '<b>%{text}</b> bids <b>%{width} MWh</b> on the spot market at <b>%{y} €/MWh</b><br> '
                'instead of their marginal cost of <b>%{meta} €/MWh</b> because they anticipate being <br>'
                'able to earn this higher price on the redispatch market.',
            
                '<b>%{width}</b> MW zu <br><b>%{y}</b> €/MWh']
        mo_df['x_pos'] = mo_df.cap.cumsum() - 0.5*mo_df.cap
        
    else:
        conditions = [(mo_df['bid'] != mo_df['WTP']) & (mo_df['Node'] == 1), (mo_df['bid']
                                                                          != mo_df['WTP']) & (mo_df['Node'] == 2), mo_df['bid'] == mo_df['WTP']]
        # width, y, meta = format(width,'.2f'), format(y,'.2f'), format(meta,'.2f') 
        values = ['<b>%{text}</b> bids <b>%{width} MWh</b> on the spot market at <b>%{y} €/MWh</b><br>'
              'instead of their willingness to pay of <b>%{meta} €/MWh</b> because they anticipate being<br>'
              'able to buy the energy on the redispatch market for this cheaper price anyway.',

              '<b>%{text}</b> bids <b>%{width} MWh</b> on the spot market at <b>%{y} €/MW</b><br>'
              'instead of their willingness to pay of <b>%{meta} €/MWh</b> because they anticipate high<br>'
              'compensation payments at the redispatch market for being downdispatched.',
              '<b>%{width}</b> MW zu <br><b>%{y}</b> €/MWh']
        mo_df['x_pos'] = mo_df.Load.cumsum() - 0.5*mo_df.Load
        
        
    mo_df['hover_template'] = np.select(conditions, values)
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
    fig = plot_function(mo_df,mo,dd_merit,ud_merit,ud_price,dd_price,clearing_price,rd_dem_dd,rd_dem_ud,type = board, load_mw = load_mw, redispatch_pricing = redispatch_pricing )
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
    cap_cons = ""
    if on:
        val = True
    else:
        val = False
    if os.path.exists("./payoff_export_dataframe.csv") and counter-n_clicks<=0:
        payoff_export_dataframe = pd.read_csv("./payoff_export_dataframe.csv")
        payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Load(MW)']] = load_mw
        payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Line Capacity(MW)']] = capacity_mw
        payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Anticipation']] = val 
        payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Redispatch Pricing']] = redispatch_pricing
        payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Mitigation Strategy']] =  f"{strategy}({sel})"
        if len(error_message) <= 5:
            payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Redispatch Payment']] = str(sum_amount) +"€" 
            payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Total Costs']] = str(spot)+"€" 
        else:
            payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Redispatch Payment']] = "---"
            payoff_export_dataframe.loc[len(payoff_export_dataframe)-1,['Total Costs']] = "---"
        payoff_export_dataframe = payoff_export_dataframe[payoff_export_dataframe['Load(MW)'].notna()]
        payoff_export_dataframe.to_csv("./payoff_export_dataframe.csv",index = False)
        counter = n_clicks + 1
    
    if sum_amount == 'nan':
                sum_amount = 0
    if len(error_message) <= 5:
        
        cap_cons = f"The limited transmission capacity of {capacity_mw} MW requires a redispatch amount of {rd_dem} MWh costing the network operator a total of {sum_amount}€. Total payments for energy equal {spot}€."
    rd_dem = format(rd_dem, '.2f')
    line_flow_end = 0
    print()
    if type == 'gen':
        line_flow_end = mo_df[mo_df.node == 1]['prod'].sum()
        text_box_summary = f"The scenario results in a power flow of {line_flow_end} MW from Node 1 to Node 2 causing a redispatch demand of {rd_dem[0:-3]} MWh"
    else:
        line_flow_end = mo_df[mo_df.Node == 2]['power_receive'].sum()
        text_box_summary = f"The scenario results in a power flow of {line_flow_end} MW from Node 1 to Node 2 causing a redispatch demand of {rd_dem[0:-3]} MWh"
        
   
    
    print_ud = error_message
    print_dd = ""       
    mo_df = mo_df.reset_index()  
    mo_df['payoff'] = mo_df['payoff'].map('{:,.2f}€'.format)
    print(mo_df.head(6))
    payoff_table =  mo_df[['name','payoff']].sort_values(by = 'name')
    payoff_table = payoff_table.set_index('name').transpose()
    payoff_table  = payoff_table.to_dict('records')
    if os.path.exists("./payoff_export_dataframe.csv"):
        
        payoff_export_dataframe =  pd.read_csv("./payoff_export_dataframe.csv")
        if type != 'gen':
            payoff_export_dataframe = payoff_export_dataframe.rename(columns = {"Load(MW)": "Power Generated(MW"})
        payoff_export_dataframe = payoff_export_dataframe.to_dict('records')
    else:
        payoff_export_dataframe = pd.DataFrame()
        payoff_export_dataframe = payoff_export_dataframe.to_dict('records')
    
    
    return fig,  print_ud, print_dd, payoff_table,payoff_export_dataframe, cap_cons,strategy_box_text, text_box,style,style_1,sanction_output,counter,text_box_summary