import dash
import os
import dash_bootstrap_components as dbc
from dash import html, dcc
import os
os.environ["PYHtON_VERSION"] = "3.9.0"

app = dash.Dash(
    __name__,  external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True
)


PLOTLY_LOGO = "https://thumbs.dreamstime.com/b/slot-machine-jackpot-icon-casino-concept-dark-background-slot-machine-jackpot-icon-casino-concept-dark-background-simple-117459826.jpg"
app.config['suppress_callback_exceptions'] = True

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Div(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        
                        dbc.Col(dbc.Button("unIT-e²", href="https://unit-e2.de/", external_link = True,className="button_offset"), className="button_div"),
                        dbc.Col(dbc.NavbarBrand("Inc-Dec Gaming Dashboards"), className = "navbar_heading")
                        
                    ],
                    
                    className="flex-grow-1",
                ),
                
            ),
             dbc.DropdownMenu(
        [
            dbc.DropdownMenuItem(page["name"], href=page["path"])
            for page in dash.page_registry.values()
            
            #if page["module"] != "pages.not_found_404"
        ],
        nav=True,
        label="More Dashboards",
        
    )
        ]
    ),
    color="dark",
    dark=True,
    className= "custom_navbar"
)


app.layout = dbc.Container(
    [navbar, dash.page_container],
    fluid=True,
)


if __name__ == "__main__":
    app.run_server(debug=True)
