import dash
from dash import html, dcc, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Cargar datos
print("Cargando datos...")

# Datos de mortalidad no fetal 2019
df_mortality = pd.read_excel('Anexos/Anexo1.NoFetal2019_CE_15-03-23.xlsx')

# Códigos de causas de muerte - ajustar según estructura real
try:
    df_codes = pd.read_excel('Anexos/Anexo2.CodigosDeMuerte_CE_15-03-23.xlsx')
    print(f"Códigos de causas cargados: {len(df_codes)} registros")
except Exception as e:
    print(f"Error cargando códigos de causas: {e}")
    df_codes = pd.DataFrame()  # DataFrame vacío como fallback

# División político-administrativa
df_divipola = pd.read_excel('Anexos/Divipola_CE_.xlsx')

print("Datos cargados exitosamente")
print(f"Registros de mortalidad: {len(df_mortality)}")
print(f"Registros Divipola: {len(df_divipola)}")

# Ajustar nombres de columnas en df_mortality
df_mortality = df_mortality.rename(columns={
    'COD_DEPARTAMENTO': 'COD_DPTO',
    'COD_MUNICIPIO': 'COD_MUNIC',
    'AO': 'ANO',
    'COD_MUERTE': 'CAUSA_DEFUNCION'
})

# Renombrar columnas para consistencia
df_divipola = df_divipola.rename(columns={
    'COD_DEPARTAMENTO': 'COD_DPTO',
    'DEPARTAMENTO': 'NOM_DPTO',
    'COD_MUNICIPIO': 'COD_MUNIC',
    'MUNICIPIO': 'NOM_MUNIC'
})

# Agregar columnas de nombres de departamento y municipio desde Divipola
df_mortality = df_mortality.merge(df_divipola[['COD_DPTO', 'NOM_DPTO', 'COD_MUNIC', 'NOM_MUNIC']].drop_duplicates(),
                                 left_on=['COD_DPTO', 'COD_MUNIC'],
                                 right_on=['COD_DPTO', 'COD_MUNIC'],
                                 how='left')

# Manejar valores NaN en NOM_DPTO
df_mortality['NOM_DPTO'] = df_mortality['NOM_DPTO'].fillna('Desconocido')
df_mortality['NOM_MUNIC'] = df_mortality['NOM_MUNIC'].fillna('Desconocido')

# Estilos CSS personalizados
external_stylesheets = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
]

# Crear aplicación Dash
app = dash.Dash(__name__, title='Análisis de Mortalidad Colombia 2019',
                external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

# Layout organizado
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.H1('📊 Análisis de Mortalidad en Colombia 2019', style={
                'color': '#2c3e50',
                'textAlign': 'center',
                'marginBottom': '10px',
                'fontSize': '2.8rem',
                'fontWeight': 'bold'
            }),
            html.P('Basado en Datos Oficiales del DANE', style={
                'color': '#7f8c8d',
                'textAlign': 'center',
                'fontSize': '1.2rem',
                'marginBottom': '30px'
            })
        ], className='col-12')
    ], className='row justify-content-center mb-5'),

    # Panel de Control - Filtros Interactivos
    html.Div([
        html.Div([
            html.Div([
                html.H4('🎛️ Panel de Control', className='text-primary mb-4'),
                html.Div([
                    html.Div([
                        html.Label('🏛️ Filtrar por Departamento:', className='form-label fw-bold'),
                        dcc.Dropdown(
                            id='departamento-filter',
                            options=[{'label': '📍 Todos los Departamentos', 'value': 'all'}] +
                                   [{'label': f'📍 {dept}', 'value': dept} for dept in sorted(df_mortality['NOM_DPTO'].dropna().unique())],
                            value='all',
                            className='mb-3',
                            style={'fontSize': '14px'}
                        ),
                    ], className='col-md-4 mb-3'),
                    html.Div([
                        html.Label('👥 Filtrar por Sexo:', className='form-label fw-bold'),
                        dcc.Dropdown(
                            id='sexo-filter',
                            options=[
                                {'label': '👥 Todos los Sexos', 'value': 'all'},
                                {'label': '👨 Masculino', 'value': '1'},
                                {'label': '👩 Femenino', 'value': '2'},
                                {'label': '⚧ Indeterminado', 'value': '3'}
                            ],
                            value='all',
                            className='mb-3',
                            style={'fontSize': '14px'}
                        ),
                    ], className='col-md-4 mb-3'),
                    html.Div([
                        html.Label([
                            '🎂 Filtrar por Grupo de Edad:',
                            html.I(className="fas fa-info-circle ml-2", id="edad-tooltip",
                                   style={'cursor': 'pointer', 'color': '#007bff'})
                        ], className='form-label fw-bold d-flex align-items-center'),
                        dcc.Dropdown(
                            id='edad-filter',
                            options=[{'label': '🎂 Todos los Grupos', 'value': 'all'}] +
                                   [{'label': f'🎂 {grupo}', 'value': grupo} for grupo in sorted(df_mortality['GRUPO_EDAD1'].dropna().unique())],
                            value='all',
                            className='mb-3',
                            style={'fontSize': '14px'}
                        ),
                        html.Div(id="tooltip-modal", children=[
                            html.Div([
                                html.Div([
                                    html.Button("×", id="close-tooltip", style={
                                        'position': 'absolute',
                                        'top': '10px',
                                        'right': '15px',
                                        'background': 'none',
                                        'border': 'none',
                                        'fontSize': '24px',
                                        'cursor': 'pointer',
                                        'color': '#666',
                                        'zIndex': '1001'
                                    }),
                                    html.H5("Referencia de Grupos de Edad", style={
                                        'marginBottom': '20px',
                                        'color': '#333',
                                        'textAlign': 'center'
                                    }),
                                    html.Table([
                                        html.Tr([html.Th("Código"), html.Th("Categoría"), html.Th("Rango de Edad")]),
                                        html.Tr([html.Td("0-4"), html.Td("Mortalidad neonatal"), html.Td("Menor de 1 mes")]),
                                        html.Tr([html.Td("5-6"), html.Td("Mortalidad infantil"), html.Td("1 a 11 meses")]),
                                        html.Tr([html.Td("7-8"), html.Td("Primera infancia"), html.Td("1 a 4 años")]),
                                        html.Tr([html.Td("9-10"), html.Td("Niñez"), html.Td("5 a 14 años")]),
                                        html.Tr([html.Td("11"), html.Td("Adolescencia"), html.Td("15 a 19 años")]),
                                        html.Tr([html.Td("12-13"), html.Td("Juventud"), html.Td("20 a 29 años")]),
                                        html.Tr([html.Td("14-16"), html.Td("Adultez temprana"), html.Td("30 a 44 años")]),
                                        html.Tr([html.Td("17-19"), html.Td("Adultez intermedia"), html.Td("45 a 59 años")]),
                                        html.Tr([html.Td("20-24"), html.Td("Vejez"), html.Td("60 a 84 años")]),
                                        html.Tr([html.Td("25-28"), html.Td("Longevidad/Centenarios"), html.Td("85 a 100+ años")]),
                                        html.Tr([html.Td("29"), html.Td("Edad desconocida"), html.Td("Sin información")]),
                                    ], className="table table-sm table-bordered", style={'fontSize': '14px'})
                                ], style={
                                    'backgroundColor': 'white',
                                    'padding': '25px',
                                    'borderRadius': '10px',
                                    'boxShadow': '0 8px 25px rgba(0,0,0,0.3)',
                                    'maxWidth': '600px',
                                    'width': '100%',
                                    'position': 'relative'
                                })
                            ], style={
                                'position': 'fixed',
                                'top': '0',
                                'left': '0',
                                'width': '100%',
                                'height': '100%',
                                'backgroundColor': 'rgba(0,0,0,0.5)',
                                'display': 'flex',
                                'justifyContent': 'center',
                                'alignItems': 'center',
                                'zIndex': '1000'
                            }, id="tooltip-overlay")
                        ], style={'display': 'none'})
                    ], className='col-md-4 mb-3'),
                ], className='row')
            ], className='card-body')
        ], className='card shadow-sm mb-5')
    ], className='container-fluid mb-5'),

    # Métricas Principales
    html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-skull-crossbones fa-3x", style={'color': '#ffffff'}),
                    html.H2(id='total-muertes', style={'color': '#ffffff', 'margin': '15px 0 5px 0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P('Total de Muertes', style={'color': '#ffffff', 'margin': '0', 'fontSize': '1rem', 'fontWeight': '500'})
                ], className='text-center p-4')
            ], className='card h-100 shadow-sm border-0', style={'background': 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)'})
        ], className='col-md-3 mb-4'),
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-mars fa-3x", style={'color': '#ffffff'}),
                    html.H2(id='muertes-hombres', style={'color': '#ffffff', 'margin': '15px 0 5px 0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P('Muertes Masculinas', style={'color': '#ffffff', 'margin': '0', 'fontSize': '1rem', 'fontWeight': '500'})
                ], className='text-center p-4')
            ], className='card h-100 shadow-sm border-0', style={'background': 'linear-gradient(135deg, #3498db 0%, #2980b9 100%)'})
        ], className='col-md-3 mb-4'),
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-venus fa-3x", style={'color': '#ffffff'}),
                    html.H2(id='muertes-mujeres', style={'color': '#ffffff', 'margin': '15px 0 5px 0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P('Muertes Femeninas', style={'color': '#ffffff', 'margin': '0', 'fontSize': '1rem', 'fontWeight': '500'})
                ], className='text-center p-4')
            ], className='card h-100 shadow-sm border-0', style={'background': 'linear-gradient(135deg, #e84393 0%, #c0392b 100%)'})
        ], className='col-md-3 mb-4'),
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-city fa-3x", style={'color': '#ffffff'}),
                    html.H2(id='deptos-afectados', style={'color': '#ffffff', 'margin': '15px 0 5px 0', 'fontSize': '2.5rem', 'fontWeight': 'bold'}),
                    html.P('Departamentos', style={'color': '#ffffff', 'margin': '0', 'fontSize': '1rem', 'fontWeight': '500'})
                ], className='text-center p-4')
            ], className='card h-100 shadow-sm border-0', style={'background': 'linear-gradient(135deg, #00b894 0%, #27ae60 100%)'})
        ], className='col-md-3 mb-4')
    ], className='row justify-content-center mb-5'),
    html.Div([
        html.P('*Los datos se actualizan automáticamente según los filtros aplicados', className='text-muted mt-2 small')
    ], className='container-fluid'),

    # Sección 1: Distribución Geográfica
    html.Div([
        html.Div([
            html.H3('📍 Distribución Geográfica de la Mortalidad', className='text-center text-primary mb-4'),
            html.Div([
                html.Div([
                    dcc.Graph(
                        id='mapa-departamentos',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '500px'}
                    )
                ], className='card shadow-sm'),
            ], className='col-12')
        ], className='row mb-5')
    ], className='container-fluid'),

    # Sección 2: Análisis Temporal
    html.Div([
        html.Div([
            html.H3('📈 Análisis Temporal', className='text-center text-success mb-4'),
            html.Div([
                html.Div([
                    html.H5('Tendencia Mensual de Muertes', className='card-title text-center'),
                    dcc.Graph(
                        id='lineas-meses',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '400px'}
                    )
                ], className='card shadow-sm p-3 mb-4')
            ], className='col-12')
        ], className='row mb-5')
    ], className='container-fluid'),

    # Sección 3: Análisis de Violencia
    html.Div([
        html.Div([
            html.H3('🔪 Análisis de Violencia y Seguridad', className='text-center text-danger mb-4'),
            html.Div([
                html.Div([
                    html.H5('Ciudades Más Violentas (Homicidios)', className='card-title text-center'),
                    dcc.Graph(
                        id='barras-violentas',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '400px'}
                    )
                ], className='card shadow-sm p-3 mb-4')
            ], className='col-md-6'),
            html.Div([
                html.Div([
                    html.H5('Ciudades Más Seguras (Menor Mortalidad)', className='card-title text-center'),
                    dcc.Graph(
                        id='circular-menor-mortalidad',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '400px'}
                    )
                ], className='card shadow-sm p-3 mb-4')
            ], className='col-md-6')
        ], className='row mb-5')
    ], className='container-fluid'),

    # Sección 4: Causas de Muerte
    html.Div([
        html.Div([
            html.H3('⚕️ Principales Causas de Muerte', className='text-center text-warning mb-4'),
            html.Div([
                html.Div([
                    dash_table.DataTable(
                        id='tabla-causas',
                        columns=[
                            {'name': '🏷️ Código CIE-10', 'id': 'codigo'},
                            {'name': '📋 Descripción', 'id': 'causa'},
                            {'name': '📊 Casos Reportados', 'id': 'total'}
                        ],
                        style_table={
                            'overflowX': 'auto',
                            'borderRadius': '10px',
                            'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.1)'
                        },
                        style_cell={
                            'textAlign': 'left',
                            'padding': '15px',
                            'fontSize': '14px',
                            'border': '1px solid #dee2e6',
                            'backgroundColor': 'white'
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold',
                            'border': '2px solid #dee2e6',
                            'textAlign': 'center',
                            'fontSize': '16px',
                            'color': '#495057'
                        },
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                            {'if': {'row_index': 'even'}, 'backgroundColor': 'white'}
                        ],
                        page_size=10,
                        style_as_list_view=True
                    )
                ], className='card shadow-sm p-4')
            ], className='col-12')
        ], className='row mb-5')
    ], className='container-fluid'),

    # Sección 5: Análisis Demográfico
    html.Div([
        html.Div([
            html.H3('👥 Análisis Demográfico', className='text-center text-info mb-4'),
            html.Div([
                html.Div([
                    html.H5('Distribución por Sexo y Departamento', className='card-title text-center'),
                    dcc.Graph(
                        id='barras-apiladas-sexo',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '500px'}
                    )
                ], className='card shadow-sm p-3 mb-4')
            ], className='col-md-6'),
            html.Div([
                html.Div([
                    html.H5('Distribución por Grupos de Edad', className='card-title text-center'),
                    dcc.Graph(
                        id='histograma-edad',
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '500px'}
                    )
                ], className='card shadow-sm p-3 mb-4')
            ], className='col-md-6')
        ], className='row mb-5')
    ], className='container-fluid'),

    # Footer
    html.Div([
        html.Div([
            html.Hr(style={'border': '1px solid #dee2e6', 'margin': '40px 0'}),
            html.Div([
                html.Div([
                    html.H6('📊 Fuente de Datos', className='text-muted mb-2'),
                    html.P('Departamento Administrativo Nacional de Estadística (DANE)', className='mb-0 small'),
                    html.P('Estadísticas Vitales 2019', className='mb-0 small')
                ], className='col-md-4'),
                html.Div([
                    html.H6('🛠️ Tecnologías', className='text-muted mb-2'),
                    html.P('Python + Dash + Plotly + Pandas', className='mb-0 small'),
                    html.P('Desplegado en Render.com', className='mb-0 small')
                ], className='col-md-4'),
                html.Div([
                    html.H6('📅 Última Actualización', className='text-muted mb-2'),
                    html.P('Noviembre 2025', className='mb-0 small'),
                    html.P('Versión 1.0.0', className='mb-0 small')
                ], className='col-md-4')
            ], className='row text-center'),
            html.P('🔍 Aplicación desarrollada para el análisis de datos de mortalidad en Colombia', className='text-center text-muted mt-4 mb-0 small')
        ], className='container')
    ], style={'backgroundColor': '#f8f9fa', 'padding': '40px 0', 'marginTop': '60px'})
], style={
    'backgroundColor': '#ffffff',
    'minHeight': '100vh',
    'fontFamily': '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif'
})

# Callbacks para actualizar gráficos
@app.callback(
    [dash.Output('total-muertes', 'children'),
     dash.Output('muertes-hombres', 'children'),
     dash.Output('muertes-mujeres', 'children'),
     dash.Output('deptos-afectados', 'children'),
     dash.Output('tooltip-modal', 'style')],
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value'),
     dash.Input('edad-tooltip', 'n_clicks'),
     dash.Input('close-tooltip', 'n_clicks')]
)
def update_stats(departamento, sexo, edad, tooltip_clicks, close_clicks):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Calcular estadísticas
    total_muertes = len(filtered_df)
    muertes_hombres = len(filtered_df[filtered_df['SEXO'] == 1])
    muertes_mujeres = len(filtered_df[filtered_df['SEXO'] == 2])
    deptos_afectados = filtered_df['COD_DPTO'].nunique()

    # Manejar tooltip modal
    ctx = dash.callback_context
    tooltip_style = {'display': 'none'}

    if ctx.triggered:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if trigger_id == 'edad-tooltip':
            tooltip_style = {'display': 'block'}
        elif trigger_id == 'close-tooltip':
            tooltip_style = {'display': 'none'}

    return f"{total_muertes:,}", f"{muertes_hombres:,}", f"{muertes_mujeres:,}", f"{deptos_afectados}", tooltip_style

@app.callback(
    dash.Output('mapa-departamentos', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_map(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Agrupar por departamento
    dept_data = filtered_df.groupby('COD_DPTO').size().reset_index(name='muertes')

    # Unir con nombres de departamentos
    dept_data = dept_data.merge(df_divipola[['COD_DPTO', 'NOM_DPTO']].drop_duplicates(),
                                on='COD_DPTO', how='left')

    # Crear mapa usando scatter con coordenadas
    fig = px.bar(dept_data,
                  x='NOM_DPTO',
                  y='muertes',
                  color='muertes',
                  color_continuous_scale='Reds')
    fig.update_layout(
        title='Distribución de Muertes por Departamento',
        xaxis_title='Departamento',
        yaxis_title='Número de Muertes',
        showlegend=False
    )
    fig.update_xaxes(tickangle=45)

    return fig

@app.callback(
    dash.Output('lineas-meses', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_line_chart(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Agrupar por mes
    monthly_data = filtered_df.groupby('MES').size().reset_index(name='muertes')

    # Nombres de meses
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    monthly_data['mes_nombre'] = monthly_data['MES'].apply(lambda x: meses[x-1] if 1 <= x <= 12 else 'Desconocido')

    fig = px.line(monthly_data, x='mes_nombre', y='muertes',
                  markers=True)
    fig.update_layout(
        title='Muertes por Mes en Colombia 2019',
        xaxis_title='Mes',
        yaxis_title='Número de Muertes',
        showlegend=False
    )

    return fig

@app.callback(
    dash.Output('barras-violentas', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_violent_cities(departamento, sexo, edad):
    # Filtrar homicidios (códigos que empiecen con X95)
    violent_deaths = df_mortality[df_mortality['CAUSA_DEFUNCION'].astype(str).str.startswith('X95', na=False)]

    # Aplicar filtros adicionales
    if departamento != 'all':
        violent_deaths = violent_deaths[violent_deaths['NOM_DPTO'] == departamento]

    if sexo != 'all':
        violent_deaths = violent_deaths[violent_deaths['SEXO'].astype(str) == sexo]

    if edad != 'all':
        violent_deaths = violent_deaths[violent_deaths['GRUPO_EDAD1'] == edad]

    # Agrupar por municipio
    city_violence = violent_deaths.groupby(['COD_DPTO', 'COD_MUNIC']).size().reset_index(name='homicidios')

    # Unir con nombres de municipios
    city_violence = city_violence.merge(df_divipola[['COD_DPTO', 'COD_MUNIC', 'NOM_MUNIC']].drop_duplicates(),
                                        on=['COD_DPTO', 'COD_MUNIC'], how='left')

    # Top 5 ciudades más violentas
    top_violent = city_violence.nlargest(5, 'homicidios')

    fig = px.bar(top_violent, x='NOM_MUNIC', y='homicidios',
                  color='homicidios', color_continuous_scale='Reds')
    fig.update_layout(
        title='5 Ciudades Más Violentas (Homicidios)',
        xaxis_title='Ciudad',
        yaxis_title='Número de Homicidios',
        showlegend=False
    )

    return fig

@app.callback(
    dash.Output('circular-menor-mortalidad', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_low_mortality_cities(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Agrupar por municipio
    city_mortality = filtered_df.groupby(['COD_DPTO', 'COD_MUNIC']).size().reset_index(name='muertes')

    # Unir con nombres
    city_mortality = city_mortality.merge(df_divipola[['COD_DPTO', 'COD_MUNIC', 'NOM_MUNIC']].drop_duplicates(),
                                         on=['COD_DPTO', 'COD_MUNIC'], how='left')

    # 10 ciudades con menor mortalidad 
    low_mortality = city_mortality[city_mortality['muertes'] >= 5].nsmallest(10, 'muertes')

    fig = px.pie(low_mortality, values='muertes', names='NOM_MUNIC')
    fig.update_layout(
        title='10 Ciudades con Menor Índice de Mortalidad',
        showlegend=True
    )
    fig.update_traces(
        textposition='inside',
        textinfo='label+value+percent',
        textfont_size=12,
        hovertemplate='<b>%{label}</b><br>Muertes: %{value}<br>Porcentaje: %{percent}<extra></extra>'
    )

    return fig

@app.callback(
    dash.Output('tabla-causas', 'data'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_causes_table(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Agrupar por causa de defunción
    causes_data = filtered_df.groupby('CAUSA_DEFUNCION').size().reset_index(name='total')

    # Crear diccionario de mapeo usando las columnas correctas del archivo de códigos
    # Basándonos en el análisis, las columnas correctas son diferentes
    if 'CODIGO_CIE10' in df_codes.columns and 'DESCRIPCION_CIE10' in df_codes.columns:
        # Si existen las columnas esperadas, usarlas
        code_mapping = dict(zip(
            df_codes['CODIGO_CIE10'].astype(str).str.strip(),
            df_codes['DESCRIPCION_CIE10'].astype(str).str.strip()
        ))
    else:
        # Buscar automáticamente las columnas correctas
        mortality_codes = set(df_mortality['CAUSA_DEFUNCION'].dropna().astype(str).str.strip().unique())

        # Encontrar la columna con mejor coincidencia para códigos
        best_code_col = None
        max_matches = 0
        best_desc_col = None

        for code_col in df_codes.columns:
            if df_codes[code_col].notna().sum() > 0:
                mapping_codes = set(df_codes[code_col].dropna().astype(str).str.strip().unique())
                matches = len(mortality_codes.intersection(mapping_codes))
                if matches > max_matches:
                    max_matches = matches
                    best_code_col = code_col

        # Encontrar columna de descripción correspondiente
        for desc_col in df_codes.columns:
            if 'DESCRIP' in desc_col.upper() or 'NOMBRE' in desc_col.upper() or 'CAUSA' in desc_col.upper():
                best_desc_col = desc_col
                break

        # Crear un mapeo combinado de TODAS las columnas que contienen códigos
        combined_mapping = {}

        # Buscar todas las columnas que contienen códigos CIE-10
        code_columns = []
        for col in df_codes.columns:
            if df_codes[col].notna().sum() > 0:
                sample = str(df_codes[col].dropna().iloc[0])
                # Si parece un código CIE-10 (letras + números, longitud razonable)
                if len(sample) <= 10 and any(c.isalpha() for c in sample) and any(c.isdigit() for c in sample):
                    code_columns.append(col)

        # Encontrar columna de descripción
        desc_col = None
        for col in df_codes.columns:
            if 'DESCRIP' in col.upper() or 'NOMBRE' in col.upper() or 'CAUSA' in col.upper():
                desc_col = col
                break

        # Crear mapeo combinado filtrado (solo descripciones no vacías)
        if code_columns and desc_col:
            for code_col in code_columns:
                # Filtrar filas con descripciones válidas (no vacías ni NaN)
                valid_rows = df_codes[
                    (df_codes[code_col].notna()) &
                    (df_codes[desc_col].notna()) &
                    (df_codes[desc_col].astype(str).str.strip() != '')
                ]

                if not valid_rows.empty:
                    temp_mapping = dict(zip(
                        valid_rows[code_col].astype(str).str.strip(),
                        valid_rows[desc_col].astype(str).str.strip()
                    ))
                    combined_mapping.update(temp_mapping)
            code_mapping = combined_mapping
        else:
            # Último fallback
            code_mapping = {
                'I219': 'Infarto agudo del miocardio',
                'J449': 'Enfermedad pulmonar obstructiva crónica',
                'C349': 'Cáncer de pulmón',
                'I64': 'Accidente cerebrovascular',
                'I10': 'Hipertensión esencial',
                'C509': 'Cáncer de mama',
                'C61': 'Cáncer de próstata',
                'E149': 'Diabetes mellitus no especificada',
                'K729': 'Enfermedad hepática',
                'X95': 'Homicidio'
            }

    # Agregar descripciones usando el mapeo automático
    causes_data['descripcion'] = causes_data['CAUSA_DEFUNCION'].astype(str).str.strip().map(code_mapping).fillna('Causa no especificada')

    # Para los códigos que aún no tienen descripción, proporcionar descripciones manuales
    manual_descriptions = {
        'J440': 'Enfermedad pulmonar obstructiva crónica con exacerbación aguda',
        'J189': 'Neumonía, no especificada',
        'C169': 'Cáncer de estómago, parte no especificada',
        'X954': 'Homicidio y lesiones por intervención legal, no especificadas'
    }

    # Aplicar descripciones manuales donde falten
    causes_data['descripcion'] = causes_data.apply(
        lambda row: manual_descriptions.get(str(row['CAUSA_DEFUNCION']).strip(), row['descripcion']),
        axis=1
    )

    # Top 10 causas
    top_causes = causes_data.nlargest(10, 'total')[['CAUSA_DEFUNCION', 'descripcion', 'total']]
    top_causes.columns = ['codigo', 'causa', 'total']

    return top_causes.to_dict('records')

@app.callback(
    dash.Output('barras-apiladas-sexo', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_stacked_sex_chart(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Agrupar por departamento y sexo
    sex_dept_data = filtered_df.groupby(['COD_DPTO', 'SEXO']).size().reset_index(name='muertes')

    # Unir con nombres de departamentos
    sex_dept_data = sex_dept_data.merge(df_divipola[['COD_DPTO', 'NOM_DPTO']].drop_duplicates(),
                                       on='COD_DPTO', how='left')

    # Mapear sexo
    sex_dept_data['SEXO'] = sex_dept_data['SEXO'].map({1: 'Masculino', 2: 'Femenino', 3: 'Indeterminado'})

    fig = px.bar(sex_dept_data, x='NOM_DPTO', y='muertes', color='SEXO',
                  barmode='stack')
    fig.update_layout(
        title='Muertes por Sexo y Departamento',
        xaxis_title='Departamento',
        yaxis_title='Número de Muertes'
    )

    return fig

@app.callback(
    dash.Output('histograma-edad', 'figure'),
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_age_histogram(departamento, sexo, edad):
    # Filtrar datos según selecciones
    filtered_df = df_mortality.copy()

    if departamento != 'all':
        filtered_df = filtered_df[filtered_df['NOM_DPTO'] == departamento]

    if sexo != 'all':
        filtered_df = filtered_df[filtered_df['SEXO'].astype(str) == sexo]

    if edad != 'all':
        filtered_df = filtered_df[filtered_df['GRUPO_EDAD1'] == edad]

    # Mapeo de grupos de edad según especificaciones
    age_groups = {
        0: 'Mortalidad neonatal',
        1: 'Mortalidad neonatal',
        2: 'Mortalidad neonatal',
        3: 'Mortalidad neonatal',
        4: 'Mortalidad neonatal',
        5: 'Mortalidad infantil',
        6: 'Mortalidad infantil',
        7: 'Primera infancia',
        8: 'Primera infancia',
        9: 'Niñez',
        10: 'Niñez',
        11: 'Adolescencia',
        12: 'Juventud',
        13: 'Juventud',
        14: 'Adultez temprana',
        15: 'Adultez temprana',
        16: 'Adultez temprana',
        17: 'Adultez intermedia',
        18: 'Adultez intermedia',
        19: 'Adultez intermedia',
        20: 'Vejez',
        21: 'Vejez',
        22: 'Vejez',
        23: 'Vejez',
        24: 'Vejez',
        25: 'Longevidad / Centenarios',
        26: 'Longevidad / Centenarios',
        27: 'Longevidad / Centenarios',
        28: 'Longevidad / Centenarios',
        29: 'Edad desconocida'
    }

    # Aplicar mapeo
    filtered_df['grupo_edad'] = filtered_df['GRUPO_EDAD1'].map(age_groups)

    # Contar por grupo
    age_data = filtered_df['grupo_edad'].value_counts().reset_index()
    age_data.columns = ['grupo', 'muertes']

    fig = px.bar(age_data, x='grupo', y='muertes',
                  title='Distribución de Muertes por Grupos de Edad',
                  color='muertes', color_continuous_scale='Viridis')
    fig.update_layout(
        xaxis_title='Grupo de Edad',
        yaxis_title='Número de Muertes',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    fig.update_xaxes(tickangle=45, gridcolor='lightgray')
    fig.update_yaxes(gridcolor='lightgray')

    return fig

# Para desarrollo local y Vercel
if __name__ == '__main__':
    print("Iniciando servidor...")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))

# Para Vercel (serverless)
def handler(request):
    return app.server