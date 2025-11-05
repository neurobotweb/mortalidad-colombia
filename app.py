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

# Renombrar columnas para consistencia
df_divipola = df_divipola.rename(columns={
    'COD_DEPARTAMENTO': 'COD_DPTO',
    'DEPARTAMENTO': 'NOM_DPTO',
    'COD_MUNICIPIO': 'COD_MUNIC',
    'MUNICIPIO': 'NOM_MUNIC'
})

# Ajustar nombres de columnas en df_mortality
df_mortality = df_mortality.rename(columns={
    'COD_DEPARTAMENTO': 'COD_DPTO',
    'COD_MUNICIPIO': 'COD_MUNIC',
    'AO': 'ANO',
    'COD_MUERTE': 'CAUSA_DEFUNCION'
})

# Estilos CSS personalizados
external_stylesheets = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
]

# Crear aplicación Dash
app = dash.Dash(__name__, title='Análisis de Mortalidad Colombia 2019',
                external_stylesheets=external_stylesheets,
                suppress_callback_exceptions=True)

# Layout simplificado para evitar errores de sintaxis
app.layout = html.Div([
    html.H1('Análisis de Mortalidad Colombia 2019', style={'textAlign': 'center'}),
    html.Div([
        html.Div([
            html.H3('Filtros'),
            html.Label('Departamento:'),
            dcc.Dropdown(
                id='departamento-filter',
                options=[{'label': 'Todos', 'value': 'all'}] +
                       [{'label': dept, 'value': dept} for dept in ['Bogotá', 'Antioquia', 'Valle del Cauca']],
                value='all'
            ),
            html.Label('Sexo:'),
            dcc.Dropdown(
                id='sexo-filter',
                options=[
                    {'label': 'Todos', 'value': 'all'},
                    {'label': 'Masculino', 'value': '1'},
                    {'label': 'Femenino', 'value': '2'}
                ],
                value='all'
            ),
        ], style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            html.H3('Estadísticas'),
            html.Div(id='total-muertes', children='Cargando...'),
            html.Div(id='muertes-hombres', children='Cargando...'),
            html.Div(id='muertes-mujeres', children='Cargando...'),
        ], style={'width': '30%', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div([
            html.H4('Distribución por Departamento'),
            dcc.Graph(id='mapa-departamentos')
        ], style={'width': '45%', 'display': 'inline-block'}),
        html.Div([
            html.H4('Tendencia Mensual'),
            dcc.Graph(id='lineas-meses')
        ], style={'width': '45%', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.Div([
            html.H4('Ciudades Más Violentas'),
            dcc.Graph(id='barras-violentas')
        ], style={'width': '45%', 'display': 'inline-block'}),
        html.Div([
            html.H4('Ciudades Más Seguras'),
            dcc.Graph(id='circular-menor-mortalidad')
        ], style={'width': '45%', 'display': 'inline-block'}),
    ]),
    html.Div([
        html.H4('Principales Causas de Muerte'),
        dash_table.DataTable(id='tabla-causas', columns=[
            {'name': 'Código', 'id': 'codigo'},
            {'name': 'Causa', 'id': 'causa'},
            {'name': 'Total', 'id': 'total'}
        ])
    ]),
    html.Div([
        html.Div([
            html.H4('Distribución por Sexo'),
            dcc.Graph(id='barras-apiladas-sexo')
        ], style={'width': '45%', 'display': 'inline-block'}),
        html.Div([
            html.H4('Distribución por Edad'),
            dcc.Graph(id='histograma-edad')
        ], style={'width': '45%', 'display': 'inline-block'}),
    ])
])

# Callbacks para actualizar gráficos
@app.callback(
    [dash.Output('total-muertes', 'children'),
     dash.Output('muertes-hombres', 'children'),
     dash.Output('muertes-mujeres', 'children'),
     dash.Output('deptos-afectados', 'children')],
    [dash.Input('departamento-filter', 'value'),
     dash.Input('sexo-filter', 'value'),
     dash.Input('edad-filter', 'value')]
)
def update_stats(departamento, sexo, edad):
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

    return f"{total_muertes:,}", f"{muertes_hombres:,}", f"{muertes_mujeres:,}", f"{deptos_afectados}"

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

    # Crear mapa usando scatter con coordenadas (simplificado)
    fig = px.bar(dept_data,
                 x='NOM_DPTO',
                 y='muertes',
                 title='Distribución de Muertes por Departamento',
                 color='muertes',
                 color_continuous_scale='Reds')
    fig.update_layout(xaxis_title='Departamento', yaxis_title='Número de Muertes')
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
                  title='Muertes por Mes en Colombia 2019',
                  markers=True)
    fig.update_layout(xaxis_title='Mes', yaxis_title='Número de Muertes')

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
                 title='5 Ciudades Más Violentas (Homicidios)',
                 color='homicidios', color_continuous_scale='Reds')
    fig.update_layout(xaxis_title='Ciudad', yaxis_title='Número de Homicidios')

    return fig

@app.callback(
    dash.Output('circular-menor-mortalidad', 'figure'),
    dash.Input('circular-menor-mortalidad', 'id')
)
def update_low_mortality_cities(_):
    # Agrupar por municipio
    city_mortality = df_mortality.groupby(['COD_DPTO', 'COD_MUNIC']).size().reset_index(name='muertes')

    # Unir con nombres
    city_mortality = city_mortality.merge(df_divipola[['COD_DPTO', 'COD_MUNIC', 'NOM_MUNIC']].drop_duplicates(),
                                         on=['COD_DPTO', 'COD_MUNIC'], how='left')

    # 10 ciudades con menor mortalidad (excluyendo valores muy bajos)
    low_mortality = city_mortality[city_mortality['muertes'] >= 5].nsmallest(10, 'muertes')

    fig = px.pie(low_mortality, values='muertes', names='NOM_MUNIC',
                 title='10 Ciudades con Menor Índice de Mortalidad')
    fig.update_traces(textposition='inside', textinfo='percent+label')

    return fig

@app.callback(
    dash.Output('tabla-causas', 'data'),
    dash.Input('tabla-causas', 'id')
)
def update_causes_table(_):
    # Agrupar por causa de defunción
    causes_data = df_mortality.groupby('CAUSA_DEFUNCION').size().reset_index(name='total')

    # Crear descripciones básicas para las causas más comunes
    cause_descriptions = {
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

    # Agregar descripciones
    causes_data['descripcion'] = causes_data['CAUSA_DEFUNCION'].astype(str).map(cause_descriptions).fillna('Causa no especificada')

    # Top 10 causas
    top_causes = causes_data.nlargest(10, 'total')[['CAUSA_DEFUNCION', 'descripcion', 'total']]
    top_causes.columns = ['codigo', 'causa', 'total']

    return top_causes.to_dict('records')

@app.callback(
    dash.Output('barras-apiladas-sexo', 'figure'),
    dash.Input('barras-apiladas-sexo', 'id')
)
def update_stacked_sex_chart(_):
    # Agrupar por departamento y sexo
    sex_dept_data = df_mortality.groupby(['COD_DPTO', 'SEXO']).size().reset_index(name='muertes')

    # Unir con nombres de departamentos
    sex_dept_data = sex_dept_data.merge(df_divipola[['COD_DPTO', 'NOM_DPTO']].drop_duplicates(),
                                       on='COD_DPTO', how='left')

    # Mapear sexo
    sex_dept_data['SEXO'] = sex_dept_data['SEXO'].map({1: 'Masculino', 2: 'Femenino', 3: 'Indeterminado'})

    fig = px.bar(sex_dept_data, x='NOM_DPTO', y='muertes', color='SEXO',
                 title='Muertes por Sexo y Departamento',
                 barmode='stack')
    fig.update_layout(xaxis_title='Departamento', yaxis_title='Número de Muertes')

    return fig

@app.callback(
    dash.Output('histograma-edad', 'figure'),
    dash.Input('histograma-edad', 'id')
)
def update_age_histogram(_):
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
    df_mortality['grupo_edad'] = df_mortality['GRUPO_EDAD1'].map(age_groups)

    # Contar por grupo
    age_data = df_mortality['grupo_edad'].value_counts().reset_index()
    age_data.columns = ['grupo', 'muertes']

    fig = px.bar(age_data, x='grupo', y='muertes',
                 title='Distribución de Muertes por Grupos de Edad',
                 color='muertes', color_continuous_scale='Blues')
    fig.update_layout(xaxis_title='Grupo de Edad', yaxis_title='Número de Muertes')
    fig.update_xaxes(tickangle=45)

    return fig

# Para desarrollo local y Vercel
if __name__ == '__main__':
    print("Iniciando servidor...")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8050)))

# Para Vercel (serverless)
def handler(request):
    return app.server