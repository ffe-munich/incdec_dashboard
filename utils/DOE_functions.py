import pandas as pd
import math
from utils.functions import redispatch, redispatch_load, payoffs, game, return_table
from utils.strategies import strategies_sel




def generator_main(input_data,anticipation,bool_var,merit_order_df,load_mw,capacity_mw ,strategy = None,gen_sel = None,sanction = 1000,redispatch_pricing = 'uniform pricing',on_freeze = False):

    """
    """
    bool_var = True
    merit_order_df = 0
    c = 1
    counter = 1
    # markups to set bids above marginal costs
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
    node1_df['node'] = 1
    node2_df['node'] = 2
    
    
    
    
    
    
    # concateante both dataframes and extend by bid column
    input_df = pd.concat([node1_df,node2_df])
    input_df['bid'] = input_df.cost+markup
    input_df.set_index(['name'],inplace=True)
    
    
 
    
    
    bool_var= True
    
    merit_order_df = 0
        
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
        
        min_node_2_cost = min_node_2_cost[min_node_2_cost.disp==0]
#         print(min_node_2_cost.head())
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
        
                
        
        mo_df = mo_df.set_index('name')
        
    
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
    
    ud_merit = ud_merit.astype({'red_bid': 'int','cost': 'int','red_bid': 'int'})
    dd_merit = dd_merit.astype({'red_bid': 'int','cost': 'int','red_bid': 'int'})
    sum_amount_with_strategy  = rd_dem * ud_price -  rd_dem * dd_price
    if redispatch_pricing == "pay-as-bid":
        sum_amount_with_strategy  = (mo_df['rd']* mo_df['red_bid']).sum()
        
    
    dd_merit['color'] = "#356CA5"
    ud_merit['color'] = "#EC9302"
    # print(mo_final.head())
    mul = clearing_price * mo_df['disp']
    spot = mul.sum()
    
    sum_amount_without_strategy = sum_amount_with_strategy
    line_flow = mo_df[mo_df.node == 1]['prod'].sum()
    
    if strategy and gen_sel and anticipation == 'Full Anticipation':
        n_clicks = 1 

        payoff_table,sum_amount_with_strategy,spot = strategies_sel(gen_sel, strategy,load_mw, mo_df, mo, dd_merit,ud_merit, rd_dem, clearing_price,capacity_mw,sum_amount_without_strategy, sanction,n_clicks,counter,anticipation, 'gen', redispatch_pricing= redispatch_pricing,return_dataframe=True)
        for j,k in payoff_table[0].items():
            
            mo_df.loc[mo_df['name'] == j, 'payoff_anticipated'] = k
        mo_df = mo_df[['name','cost','Game','node','bid','disp','rd','red_bid','left_to_disp','prod','payoff_anticipated']]
        # mo_df = mo_df.rename(columns={"payoff_anticipated": "Payoff"}, errors="raise")
#     print(mo_df.head(6)) 
    line_flow = 0

    if anticipation == 'Full Anticipation':
        mo_df = mo_df[['name','cost','Game','node','bid','disp','rd','red_bid','left_to_disp','prod','payoff_anticipated']]
        mo_df = mo_df.rename(columns={"payoff_anticipated": "Payoff"}, errors="raise")
        mo_df = mo_df.rename(columns={"bid": "Spotmarket Price","disp":"Intial Dispatch","prod":"Final Dispatch","rd":"Redispatch Demand","cost":"Cost","red_bid":"Redispatch Market Bid","name":"Name"}, errors="raise")

    else:
        mo_df = mo_df[['name','cost','Game','node','bid','disp','rd','red_bid','left_to_disp','prod','payoff_without_anticipated']]
        mo_df = mo_df.rename(columns={"payoff_without_anticipated": "Payoff"}, errors="raise")
        mo_df = mo_df.rename(columns={"bid": "Spotmarket Price","disp":"Intial Dispatch","prod":"Final Dispatch","rd":"Redispatch Demand","cost":"Cost","red_bid":"Redispatch Market Bid","name":"Name"}, errors="raise")

#     if  math.isnan(sum_amount_with_strategy):
#         spot = spot 
#     else:       
#         spot = spot + sum_amount_with_strategy
    if anticipation == 'No Anticipation':
        strategy = None
        gen_sel = None
    system_characteristics_data = pd.DataFrame(columns=['Load','Line Capacity','Line Flow','Clearing Price','Anticipation','Pricing Mechanism','Redispatch Demand','Redispatch Costs','Total Energy Payments','Strategy','Player Selected for Strategy'])
   
    l = [load_mw,capacity_mw,line_flow,clearing_price,anticipation,redispatch_pricing,rd_dem,sum_amount_with_strategy,spot,strategy,gen_sel]
    system_characteristics_data .loc[len(system_characteristics_data )] = l

    
    return mo_df,system_characteristics_data




from utils.functions import redispatch_load as redispatch_load

def load_main(input_data,anticipation,bool_var,merit_order_df,power_mw,capacity_mw ,strategy = None,load_sel = None,sanction = 1000,redispatch_pricing = 'uniform pricing',on_freeze = False):
    
    merit_order_df = 0


    # markups to set bids above marginal costs
    bool_var = True
    merit_order_df = 0
    c = 1
    counter = 1
    markup = 0

    # generate input dataframe
    input_df = pd.DataFrame(input_data)
    input_df  = input_df.replace(0, 0.0001)

    input_df['Name'] = [f"L{i+1}" for i in range(len(input_df))]

    # create dataframes for both nodes
    node1_df = input_df[['Name', 'Load', 'WTP', 'Game','Node']][input_df.Node == 1]
    node2_df = input_df[['Name', 'Load', 'WTP', 'Game','Node']][input_df.Node == 2]
    payoff_df = pd.DataFrame(columns=input_df['Name'])
    
    
   

    #anticipation =  '{}'.format(on_anticipation)

    # concateante both dataframes and extend by bid column
    input_df = pd.concat([node1_df, node2_df])
    input_df['bid'] = input_df.WTP+markup
    input_df.set_index(['Name'], inplace=True)
    
    
    counter = counter


    bool_var = bool_var
    
    merit_order_df = merit_order_df
    n_clicks = 0
    if n_clicks == 0:
        counter = 1 

#    create merit order
    mo = input_df.sort_values(by='bid', ascending=False)

    if anticipation == 'No Anticipation':
        bool_var = True

    if bool_var:
        mo_1, mo_2, rd_dem, dd_price, ud_price = redispatch_load(
            mo=mo, power=power_mw, line_cap=capacity_mw,pay_as_bid = redispatch_pricing, freeze_bool = 'False')
        
        if redispatch_pricing == 'pay-as-bid':
            mo_1.red_bid = mo_1.pay_as_bid_red
            mo_2.red_bid = mo_2.pay_as_bid_red
        dd_merit = mo_2[mo_2.disp > 0]
        ud_merit = mo_1[mo_1.disp < mo_1.Load]
        mo_df = pd.concat([mo_1, mo_2])

        mo_df.sort_values(by='bid', inplace=True, ascending=False)
        clearing_price = mo_df.bid[mo_df.Load.cumsum() >= power_mw].max()
        production_line_flow = mo_df[mo_df.Node==2]['disp'].sum()
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
       
                
        mo_df = mo_df.set_index('Name')
        
        
       
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
        mo_1, mo_2, rd_dem, dd_price, ud_price = redispatch_load(
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

    # print("ud_merit")
    # print(ud_merit.head())
    ud_merit = ud_merit.astype({'red_bid': 'int','WTP': 'int','pay_as_bid_red': 'int'})
    dd_merit = dd_merit.astype({'red_bid': 'int','WTP': 'int','pay_as_bid_red': 'int'})
    
         
   
   
    
    dd_merit['color'] = "#EC9302"
    ud_merit['color'] = "#356CA5"
     
    sum_amount_with_strategy  = rd_dem * ud_price -  rd_dem * dd_price
    mul = clearing_price * mo_df['disp']
   
    spot = mul.sum()
    if redispatch_pricing == "pay-as-bid":
        sum_amount_with_strategy  = (mo_df['rd']* mo_df['red_bid']).sum()
    sum_amount_without_strategy = sum_amount_with_strategy
    if strategy and load_sel and anticipation == 'Full Anticipation':
        n_clicks = 1 

        payoff_table,sum_amount_with_strategy,spot = strategies_sel(load_sel, strategy,power_mw, mo_df, mo, dd_merit,ud_merit, rd_dem, clearing_price,capacity_mw,sum_amount_without_strategy, sanction,n_clicks,counter,anticipation, 'load', redispatch_pricing= redispatch_pricing,return_dataframe=True)
        for j,k in payoff_table[0].items():
            
            mo_df.loc[mo_df['name'] == j, 'payoff_anticipated'] = k
        mo_df = mo_df[['Name','WTP','Game','Node','bid','disp','rd','red_bid','left_to_receive','power_receive','payoff_anticipated']]

    if anticipation == 'Full Anticipation':
        mo_df = mo_df[['Name','WTP','Game','Node','bid','disp','rd','red_bid','left_to_receive','power_receive','payoff_anticipated']]
        mo_df = mo_df.rename(columns={"payoff_anticipated": "Payoff"}, errors="raise")
        mo_df = mo_df.rename(columns={"bid": "Spotmarket Price","disp":"Intial Dispatch","power_receive":"Final Dispatch","rd":"Redispatch Demand","red_bid":"Redispatch Market Bid"}, errors="raise")
    else:
        mo_df = mo_df[['Name','WTP','Game','Node','bid','disp','rd','red_bid','left_to_receive','power_receive','payoff_without_anticipated']]
        mo_df = mo_df.rename(columns={"payoff_without_anticipated": "Payoff"}, errors="raise")
        mo_df = mo_df.rename(columns={"bid": "Spotmarket Price","disp":"Intial Dispatch","power_receive":"Final Dispatch","rd":"Redispatch Demand","red_bid":"Redispatch Market Bid"}, errors="raise")

    if anticipation == 'No Anticipation':
        strategy = None
        load_sel = None
    system_characteristics_data = pd.DataFrame(columns=['Power Generated','Line Capacity','Clearing Price','Anticipation','Pricing Mechanism','Redispatch Demand','Redispatch Costs','Total Energy Payments','Strategy','Player Selected for Strategy'])

    l = [power_mw,capacity_mw,clearing_price,anticipation,redispatch_pricing,rd_dem,-1*sum_amount_with_strategy,spot,strategy,load_sel]
    system_characteristics_data .loc[len(system_characteristics_data )] = l

    return mo_df,system_characteristics_data
