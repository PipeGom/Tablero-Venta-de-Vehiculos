import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import os

# Carga de datos
df = pd.read_csv("Car Sales.xlsx - car_data.csv")
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
df['Month'] = df['Date'].dt.to_period('M').dt.to_timestamp()

# Agrupación por rango de ingresos
df['Income Group'] = pd.cut(
    df['Annual Income'],
    bins=[0, 50000, 100000, 200000, 500000, 1_000_000, 10_000_000],
    labels=['0-50K', '50K-100K', '100K-200K', '200K-500K', '500K-1M', '1M+']
)

# Rango de precios para heatmap
df['Price Range'] = pd.cut(
    df['Price ($)'],
    bins=[0, 20000, 40000, 60000, 80000, 100000],
    labels=['0-20K', '20K-40K', '40K-60K', '60K-80K', '80K-100K']
)

# Inicializar la app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Gráfico de líneas
fig1 = px.line(
    df.groupby('Month')['Price ($)'].sum().reset_index(),
    x='Month',
    y='Price ($)',
    title='Ventas Mensuales (USD)'
)
fig1.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([ 
                dict(count=1, label='1M', step='month', stepmode='backward'),
                dict(count=6, label='6M', step='month', stepmode='backward'),
                dict(count=1, label='1Y', step='year', stepmode='backward'),
                dict(step='all')
            ])
        ),
        rangeslider=dict(visible=True),
        type="date"
    )
)

# Dropdown para gráfico de barras
unique_years = df['Date'].dt.year.unique()
dropdown_year = dcc.Dropdown(
    options=[{'label': str(year), 'value': year} for year in unique_years],
    value=unique_years[0],
    id='dropdown-year',
    clearable=False
)

def create_bar_chart(selected_year):
    filtered = df[df['Date'].dt.year == selected_year]
    data = filtered.groupby('Company')['Price ($)'].sum().nlargest(10).reset_index()
    return px.bar(data, x='Company', y='Price ($)', title=f'Top 10 Marcas más Vendidas - {selected_year}')

def create_pie_chart(color_scheme='default'):
    colors = ['#636EFA', '#EF553B', '#00CC96'] if color_scheme == 'default' else ['#AB63FA', '#FFA15A', '#19D3F3']
    fig = px.pie(df, names='Transmission', title='Distribución por Tipo de Transmisión', color_discrete_sequence=colors)
    return fig

# Gráfico heatmap
def create_heatmap():
    pivot = df.pivot_table(index='Income Group', columns='Price Range', aggfunc='size', fill_value=0)
    fig = px.imshow(pivot, text_auto=True, title='Cantidad de Autos por Grupo de Ingreso y Rango de Precio')
    return fig

# RadioItems para seleccionar tipo de gráfico
graph_types = dcc.RadioItems(
    options=[
        {'label': 'Heatmap', 'value': 'heatmap'},
        {'label': 'Boxplot', 'value': 'box'}
    ],
    value='heatmap',
    id='radio-graph'
)

def create_graph(type_='heatmap'):
    if type_ == 'box':
        return px.box(df, x='Income Group', y='Price ($)', title='Distribución de Precio por Grupo de Ingreso')
    else:
        return create_heatmap()

# Layout
app.layout = dbc.Container([
    html.H1("Tablero de Ventas de Autos", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            dcc.Graph(figure=fig1, id='line-chart')
        ], width=6),
        dbc.Col([
            html.Label("Seleccionar Año"),
            dropdown_year,
            dcc.Graph(id='bar-chart')
        ], width=6),
    ]),

    dbc.Row([
        dbc.Col([
            html.Button("Cambiar Colores", id='color-button', n_clicks=0),
            dcc.Graph(id='pie-chart', figure=create_pie_chart())
        ], width=6),
        dbc.Col([
            html.Label("Tipo de gráfico:"),
            graph_types,
            dcc.Graph(id='income-graph', figure=create_graph())
        ], width=6)
    ])
], fluid=True)

# Callbacks
@app.callback(
    Output('bar-chart', 'figure'),
    Input('dropdown-year', 'value')
)
def update_bar_chart(selected_year):
    return create_bar_chart(selected_year)

@app.callback(
    Output('pie-chart', 'figure'),
    Input('color-button', 'n_clicks')
)
def update_pie_chart(n_clicks):
    scheme = 'default' if n_clicks % 2 == 0 else 'alt'
    return create_pie_chart(scheme)

@app.callback(
    Output('income-graph', 'figure'),
    Input('radio-graph', 'value')
)
def update_income_graph(type_):
    return create_graph(type_)

app.title = "Auto Sales Dashboard"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=True)
