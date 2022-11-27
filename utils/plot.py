import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np



def plot_function(mo_df,mo,dd_merit,ud_merit,ud_price,dd_price,clearing_price,rd_dem_dd,rd_dem_ud,type = 'gen',load_mw = 1,redispatch_pricing  = 'uniform pricing'):
    
    
    color_dict = {"1B": "#356CA5", "2C":"#F7D507", "1D":"#8AB5E1",
              "3B":"#AB2626", "1A":"#1F4E79", "4C":"#EC9302", 
              "3A": "#7A1C1C"}
    
    
    # devide into two dfs for plotting
   
    mo_north = mo_df[mo.node==1] if type == 'gen' else mo_df[mo.Node==1]
    mo_south = mo_df[mo.node==2] if type == 'gen' else mo_df[mo.Node==2]
    
    
    # create plot
    fig = make_subplots(rows=2, cols=2, subplot_titles=("Spotmarket", "Downdispatch", "Updispatch"),
                 specs=[[{"colspan": 2}, None],[{}, {}]], 
                 horizontal_spacing = 0.1, vertical_spacing = 0.15)
    
    
    
    width_var =  mo_north.cap if type == 'gen' else mo_north.Load
    meta_var =  mo_north.cost if type == 'gen' else mo_north.WTP
    meta_var = meta_var.tolist()
    width_var  = width_var .tolist()
    meta_var = [round(value,2) for value in meta_var]
    width_var = [round(value,2) for value in width_var]
    mo_north.bid = mo_north.bid.apply(lambda x: round(x, 2))
    mo_south.bid = mo_south.bid.apply(lambda x: round(x, 2))
    #width_var = width_var.map
    # add bars for node 1
    fig.add_trace(go.Bar(
        x = mo_north.x_pos,
        y = mo_north.bid,
        width = width_var,
        marker=dict(color=color_dict['1B']),
        text = mo_north.index,
        meta = meta_var,
        hovertemplate = mo_north.hover_template,
        name = 'Node 1'),
        row=1, col=1
    )
    
    
    width_var =  mo_south.cap if type == 'gen' else mo_south.Load
    meta_var =  mo_south.cost if type == 'gen' else mo_south.WTP
    updispatch_plot_axis = "Payment to power plant for UD <br>in €/MWh" if type == 'gen' else "Payment to the grid operator for UD<br> in €/MWh"
    downdispatch_plot_axis = "Payment to grid operator for DD <br>in €/MWh" if type == 'gen' else "Payment to the load for DD<br> in €/MWh"
    # add bars for node 2
    fig.add_trace(go.Bar(
        x = mo_south.x_pos,
        y = mo_south.bid,
        marker=dict(color=color_dict['4C']),
        width = width_var,
        text = mo_south.index,
        meta = meta_var,
        hovertemplate = mo_south.hover_template,
        name = 'Node 2'),
        row=1, col=1
    )
    
    # update layout
    fig.update_xaxes(title_text="MW", row=1, col='all')
    fig.update_yaxes(title_text="Market price in €/MWh", row=1, col='all')
    
    
    annotation_text_1 = "Demand in MW" if type == 'gen' else "Power generated in MW"
    annotation_text_2 = "Market price in €/MWh" if type == 'gen' else "Clearing price in €/MWh"
    
    fig.add_vline(x=load_mw, annotation_text=annotation_text_1, annotation_position='top right')
    fig.add_hline(y=clearing_price, line_dash="dash", 
                  annotation_text=annotation_text_2 , annotation_position= 'top left' if type =='gen' else 'top right')
    
      
      
    node_var =  'Node 1' if type == 'gen' else 'Node 2'
   
    ud_merit.bid = ud_merit.bid.apply(lambda x: round(x, 2))
    dd_merit.bid = dd_merit.bid.apply(lambda x: round(x, 2))  
    dd_merit.disp = dd_merit.disp.apply(lambda x: round(x, 2)) 
    dd_merit_plot = dd_merit.copy()
    
    if type =="load":
        mo_north['cap']= mo_north.Load
        mo_south['cap']= mo_south.Load
        dd_merit['cap']  = dd_merit['Load'] 
        ud_merit['cap']  = ud_merit['Load'] 
    dd_merit_cap_sum = mo_north['cap'].sum()-1    
    ud_merit_cap_sum = mo_south['cap'].sum()-1  
    if dd_merit_cap_sum < dd_merit['cap'].sum():
        dd_merit_cap_sum = dd_merit['cap'].sum()   
    if ud_merit_cap_sum < ud_merit['cap'].sum():
        ud_merit_cap_sum = ud_merit['cap'].sum()       
     
            
    # add subplot for downdispatch
    fig.add_trace(go.Bar(
        x = dd_merit_plot.disp.cumsum() - 0.5*dd_merit_plot.disp,
        y = dd_merit_plot.red_bid,
        width = dd_merit_plot.disp,
        text = dd_merit_plot.index,
        hovertemplate = dd_merit_plot.hover_template,
        name = node_var,
        showlegend=False,
        marker=dict(color=dd_merit_plot['color'].tolist())),
        row=2, col=1
    )
    
    fig.add_vline(x=rd_dem_dd, annotation_text="DD Demand", annotation_position='top left', row=2, col=1)
    if not np.isnan(dd_price):
        if redispatch_pricing == "uniform pricing":
            fig.add_hline(y=dd_price, line_dash="dash", 
                        annotation_text="DD Price in €/MWh", annotation_position='top right' if type =='gen' else 'top left', row=2, col=1)
    
    fig.update_xaxes(title_text="MW", row=1, col=1)
    lim = mo_df.cost.max() if type == 'gen' else mo_df.WTP.max()
    lim += 5 
    fig.update_yaxes(title_text=downdispatch_plot_axis, row=2, col=1)
    fig.update_yaxes(range = [0,lim], row=2, col=1)
    fig.update_yaxes(range = [0,lim], row=2, col=2)
    fig.update_yaxes(range = [0,lim], row=1, col=1)
    fig.update_xaxes(range = [0,dd_merit_cap_sum], row=2, col=1)
    fig.update_xaxes(range = [0,ud_merit_cap_sum], row=2, col=2)
    node_var =  'Node 2' if type == 'gen' else 'Node 1'
    
    width_var =  ud_merit.cap-ud_merit.disp if type == 'gen' else ud_merit.Load-ud_merit.disp
    
    width_var  = width_var .tolist()
    width_var = [round(value,2) for value in width_var]
    
    if type == 'gen':
        x_var =  ud_merit.cap.cumsum() - ud_merit.disp.cumsum() - 0.5*(ud_merit.cap - ud_merit.disp)
        
    else: 
        x_var = ud_merit.Load.cumsum() - ud_merit.disp.cumsum() - 0.5*(ud_merit.Load - ud_merit.disp)
    # add subplot for updispatch
    fig.add_trace(go.Bar(
        x = x_var,
        y = ud_merit.red_bid,
        width = width_var,
        text = ud_merit.index,
        hovertemplate = ud_merit.hover_template,
        name = node_var,
        showlegend=False,
        marker=dict(color=ud_merit['color'].tolist())),
        row=2, col=2
    )
    
    fig.add_vline(x=rd_dem_ud, annotation_text="UD Demand", annotation_position='top right', row=2, col=2)
    if not np.isnan(ud_price):
        if redispatch_pricing == "uniform pricing":
            fig.add_hline(y=ud_price, line_dash="dash", 
                        annotation_text="UD Price in €/MWh", annotation_position='top left' if type =='gen' else 'top right', row=2, col=2)
    

    fig.update_xaxes(title_text="MW", row=1, col=2)
    fig.update_yaxes(title_text=updispatch_plot_axis, row=2, col=2)
    
    fig.update_layout(autosize=False,
                      width=1000,
                      height=700,  paper_bgcolor ='#f8f9fa')
    
    
    return fig
