import dash
from dash import dcc, html, Input, Output, dash_table, ctx
import plotly.express as px
import pandas as pd
import numpy as np
import re

# ==========================================
# 1. CARREGAMENTO DOS DADOS (ENEM E SUS)
# ==========================================

# Dados do ENEM
df_enem = pd.read_excel("Enem_2024_Amostra_Perfeita.xlsx")

# Dados do SUS (Mantenha o caminho correto do seu arquivo aqui)
df_sus = pd.read_excel("CIA014_SUS_Prova_2.xlsx")


# ==========================================
# 2. PROCESSAMENTO E GRÁFICOS DO ENEM
# ==========================================

colunas_map = {
    'NOTA_CN_CIENCIAS_DA_NATUREZA': 'Nota da prova de Ciências da Natureza',
    'NOTA_CH_CIENCIAS_HUMANAS': 'Nota da prova de Ciências Humanas',
    'Idade_Calculada': 'Idade Claculada a partir da Faixa Etária',
    'NOTA_MT_MATEMATICA': 'Nota da prova de Matemática'
}

df_grafico = df_enem[list(colunas_map.keys())].rename(columns=colunas_map)
matriz_corr = df_grafico.corr()

mask = np.triu(np.ones_like(matriz_corr, dtype=bool))
matriz_corr_mascarada = matriz_corr.mask(mask)

eixo_y = ['Nota da prova de Ciências Humanas', 'Idade Claculada a partir da Faixa Etária', 'Nota da prova de Matemática']
eixo_x = ['Nota da prova de Ciências da Natureza', 'Nota da prova de Ciências Humanas', 'Idade Claculada a partir da Faixa Etária']
matriz_final = matriz_corr_mascarada.loc[eixo_y, eixo_x]

# Gráfico 1: Mapa de Calor ENEM
fig_corr = px.imshow(
    matriz_final, 
    text_auto=".2f", 
    color_continuous_scale="Blues"
)
fig_corr.update_traces(xgap=3, ygap=3)
fig_corr.update_layout(
    title='<b>Correlação de medidas selecionadas</b>', 
    title_font=dict(size=18, color='#1a202c'),
    plot_bgcolor='white', paper_bgcolor='white', 
    height=650, 
    margin=dict(l=20, r=20, t=60, b=160), 
    coloraxis_colorbar=dict(
        title="", orientation="h", yanchor="top", y=-0.35, xanchor="center", x=0.5,
        tickvals=[matriz_final.min().min(), matriz_final.max().max()], ticktext=["Fraco", "Forte"],
        len=0.5, thickness=15
    )
)
fig_corr.update_xaxes(showgrid=False, zeroline=False, tickangle=-45)
fig_corr.update_yaxes(showgrid=False, zeroline=False)

# Gráfico 2: Dispersão ENEM (Natureza x Humanas)
fig_dispersao1 = px.scatter(
    df_enem,
    x='NOTA_CN_CIENCIAS_DA_NATUREZA',
    y='NOTA_CH_CIENCIAS_HUMANAS',
    labels={
        'NOTA_CN_CIENCIAS_DA_NATUREZA': 'Nota da prova de Ciências da Natureza',
        'NOTA_CH_CIENCIAS_HUMANAS': 'Nota da prova de Ciências Humanas'
    },
    color_discrete_sequence=['#4299e1']
)
fig_dispersao1.update_traces(marker=dict(size=4, opacity=0.7))
fig_dispersao1.update_layout(
    title='<b>Gráfico de dispersão de medidas selecionadas</b>',
    title_font=dict(size=18, color='#1a202c'),
    plot_bgcolor='white', paper_bgcolor='white',
    margin=dict(l=20, r=20, t=60, b=40),
    xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False)
)

# Gráfico 3: Dispersão ENEM (Idade x Matemática)
fig_dispersao2 = px.scatter(
    df_enem,
    x='Idade_Calculada',
    y='NOTA_MT_MATEMATICA',
    labels={
        'Idade_Calculada': 'Idade Claculada a partir da Faixa Etária',
        'NOTA_MT_MATEMATICA': 'Nota da prova de Matemática'
    },
    color_discrete_sequence=['#4299e1']
)
fig_dispersao2.update_traces(marker=dict(size=4, opacity=0.7))
fig_dispersao2.update_layout(
    title='<b>Gráfico de dispersão de medidas selecionadas</b>',
    title_font=dict(size=18, color='#1a202c'),
    plot_bgcolor='white', paper_bgcolor='white',
    margin=dict(l=20, r=20, t=60, b=40),
    xaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False),
    yaxis=dict(showgrid=True, gridcolor='#e2e8f0', zeroline=False)
)


# ==========================================
# 3. TRATAMENTO DE DADOS DO SUS
# ==========================================

if df_sus['LATITUDE'].dtype == 'object':
    df_sus['LATITUDE'] = df_sus['LATITUDE'].str.replace(',', '.').astype(float)
if df_sus['LONGITUDE'].dtype == 'object':
    df_sus['LONGITUDE'] = df_sus['LONGITUDE'].str.replace(',', '.').astype(float)

df_sus['VL_Total'] = df_sus['VL_Total'].fillna(0)
df_sus['QTD_Total'] = df_sus['QTD_Total'].fillna(0)

uf_col = 'UF_NOME' if 'UF_NOME' in df_sus.columns else 'UF'
pop_col = 'Faixa_Populacao' if 'Faixa_Populacao' in df_sus.columns else 'Faixa_populacao'

df_sus['Nome_Municipio'] = df_sus['Nome_Municipio'].astype(str)
df_sus['Regiao_Nome'] = df_sus['Regiao_Nome'].astype(str)

for col in ['Nome_Municipio', 'Regiao_Nome']:
    df_sus[col] = df_sus[col].str.replace(r'0?x[0-9a-fA-F]+', ' ', regex=True, case=False)
    df_sus[col] = df_sus[col].str.replace(r'[^a-zA-ZÀ-ÿ\s]', ' ', regex=True)
    df_sus[col] = df_sus[col].str.replace(r'\b[xX]\b', ' ', regex=True) 
    df_sus[col] = df_sus[col].str.replace(r'\s+', ' ', regex=True).str.strip().str.title()

def formatar_faixa_populacao(texto):
    texto = str(texto).replace('_', ' ')
    texto = re.sub(r'0?x[0-9a-fA-F]+', ' ', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\b[xX]\b', ' ', texto)
    texto = re.sub(r'\b(\d{4,8})\b', lambda m: f"{int(m.group(1)):,}".replace(',', '.'), texto)
    texto = texto.lower().replace('ate', 'Até')
    partes = [p.capitalize() if p not in ['a', 'e', 'de'] else p for p in texto.split()]
    return " ".join(partes).capitalize().strip()

df_sus[pop_col] = df_sus[pop_col].apply(formatar_faixa_populacao)


# ==========================================
# 4. CONFIGURAÇÃO DO DASH E LAYOUT EM ABAS
# ==========================================

app = dash.Dash(__name__)
server = app.server  # Crucial para o Render!

# Estilos Visuais Compartilhados
CARD_STYLE = {
    'backgroundColor': 'white', 'padding': '20px', 
    'borderRadius': '12px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.05)',
    'marginBottom': '20px'
}

TAB_STYLE = {
    'padding': '12px', 'fontWeight': '600', 'fontFamily': 'Segoe UI', 
    'backgroundColor': '#edf2f7', 'border': 'none', 'borderBottom': '1px solid #e2e8f0'
}

TAB_SELECTED_STYLE = {
    'padding': '12px', 'fontWeight': 'bold', 'fontFamily': 'Segoe UI',
    'backgroundColor': 'white', 'borderTop': '4px solid #2b6cb0', 'boxShadow': '0 -2px 4px rgba(0,0,0,0.05)'
}

app.layout = html.Div(style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'padding': '25px', 'backgroundColor': '#f4f6f9', 'minHeight': '100vh'}, children=[
    
    # Cabeçalho Principal Unificado
    html.Div(style={'backgroundColor': 'white', 'padding': '15px 25px', 'borderTop': '4px solid #2b6cb0', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'marginBottom': '25px', 'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'borderRadius': '8px'}, children=[
        html.H2("Painel Integrado de Análise de Dados", style={'margin': '0', 'color': '#1a202c', 'fontWeight': 'bold', 'fontSize': '24px'}),
        html.Div([
            html.Span("Made by ", style={'color': '#718096'}),
            html.Span("Thiago Félix", style={'fontWeight': 'bold', 'color': '#2b6cb0'})
        ], style={'fontSize': '16px'})
    ]),

    # Sistema de Abas para Separar o ENEM e o SUS
    dcc.Tabs(id="abas-principais", value='aba-enem', children=[
        
        # --- ABA 1: ENEM ---
        dcc.Tab(label='📊 Análise ENEM 2024', value='aba-enem', style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE, children=[
            html.Div(style={'paddingTop': '20px', 'display': 'flex', 'gap': '20px', 'flexDirection': 'column'}, children=[
                
                # Cartão 1: Mapa de Calor
                html.Div(style=CARD_STYLE, children=[
                    dcc.Graph(figure=fig_corr, style={'height': '650px'})
                ]),
                
                # Cartão 2: Dispersão 1
                html.Div(style=CARD_STYLE, children=[
                    dcc.Graph(figure=fig_dispersao1, style={'height': '600px'})
                ]),

                # Cartão 3: Dispersão 2 (Idade x Matemática)
                html.Div(style=CARD_STYLE, children=[
                    dcc.Graph(figure=fig_dispersao2, style={'height': '600px'})
                ])
            ])
        ]),
        
        # --- ABA 2: SUS ---
        dcc.Tab(label='🏥 Análise SUS 2023', value='aba-sus', style=TAB_STYLE, selected_style={**TAB_SELECTED_STYLE, 'borderTop': '4px solid #38a169'}, children=[
            html.Div(style={'paddingTop': '20px'}, children=[
                
                # Título interno da análise do SUS
                html.Div(style={'marginBottom': '20px'}, children=[
                    html.H3("Dashboard SUS 2023", style={'color': '#1a202c', 'margin': '0', 'fontWeight': '700'}),
                    html.H5("Análise Estratégica de Municípios e Estados", style={'color': '#718096', 'margin': '5px 0 0 0', 'fontWeight': '400'})
                ]),

                # Resumo e botão limpar do SUS
                html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'marginBottom': '20px'}, children=[
                    html.P(
                        "Verifica-se junto a amostra da base do SUS do Ano de 2023 um total de quatrocentos "
                        "e quarenta milhões de procedimentos feitos em todo o Brasil, gerando um custo total "
                        "de vinte e um Bilhões de reais investido para suprir tais procedimentos.",
                        style={'fontSize': '16px', 'color': '#4a5568', 'maxWidth': '700px', 'lineHeight': '1.5', 'margin': '0'}
                    ),
                    html.Button(
                        '🔄 Limpar Filtros Cruzados', id='btn-limpar', n_clicks=0, 
                        style={'padding': '10px 20px', 'backgroundColor': '#38a169', 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'fontWeight': 'bold', 'boxShadow': '0 2px 4px rgba(56,161,105,0.3)'}
                    )
                ]),

                # KPIs Dinâmicos do SUS
                html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '25px'}, children=[
                    html.Div(style={**CARD_STYLE, 'flex': '1', 'borderLeft': '5px solid #3182ce', 'marginBottom': '0'}, children=[
                        html.P("Quantidade Total de Procedimentos", style={'margin': '0', 'color': '#718096', 'fontSize': '14px', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                        html.H2(id='kpi-qtd', style={'margin': '10px 0 0 0', 'color': '#2d3748', 'fontSize': '32px'})
                    ]),
                    html.Div(style={**CARD_STYLE, 'flex': '1', 'borderLeft': '5px solid #38a169', 'marginBottom': '0'}, children=[
                        html.P("Valor Total dos Procedimentos", style={'margin': '0', 'color': '#718096', 'fontSize': '14px', 'fontWeight': '600', 'textTransform': 'uppercase'}),
                        html.H2(id='kpi-valor', style={'margin': '10px 0 0 0', 'color': '#2d3748', 'fontSize': '32px'})
                    ])
                ]),

                # Mapa SUS
                html.Div(style=CARD_STYLE, children=[
                    dcc.Graph(id='grafico-mapa', style={'height': '55vh'})
                ]),
                
                # Barras + Tabela SUS
                html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'}, children=[
                    html.Div(style={**CARD_STYLE, 'flex': '1', 'marginBottom': '0'}, children=[
                        dcc.Graph(id='grafico-barra-pop', style={'height': '45vh'})
                    ]),
                    
                    html.Div(style={**CARD_STYLE, 'flex': '1.2', 'marginBottom': '0'}, children=[
                        html.H4("Resumo Financeiro por Estado (UF)", style={'margin': '0 0 15px 0', 'color': '#2d3748'}),
                        dash_table.DataTable(
                            id='tabela-uf',
                            columns=[
                                {"name": "UF", "id": uf_col},
                                {"name": "Qtd Procedimentos", "id": "QTD_BR"},
                                {"name": "Valor Total", "id": "VL_BR"},
                                {"name": "Valor Médio", "id": "VM_BR"}
                            ],
                            style_table={'height': '40vh', 'overflowY': 'auto'},
                            style_cell={'textAlign': 'center', 'fontFamily': 'Segoe UI, Arial', 'padding': '10px', 'border': '1px solid #edf2f7'},
                            style_header={'backgroundColor': '#e6fffa', 'color': '#234e52', 'fontWeight': 'bold', 'borderBottom': '2px solid #b2f5ea'},
                            style_data_conditional=[
                                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f7fafc'},
                                {'if': {'filter_query': '{'+uf_col+'} = "Total"'}, 'fontWeight': 'bold', 'backgroundColor': '#e2e8f0', 'color': '#1a202c'}
                            ]
                        )
                    ])
                ])
            ])
        ])
    ])
])


# ==========================================
# 5. CALLBACK INTERATIVO (EXCLUSIVO DO SUS)
# ==========================================

@app.callback(
    [Output('grafico-mapa', 'figure'),
     Output('grafico-barra-pop', 'figure'),
     Output('tabela-uf', 'data'),
     Output('kpi-qtd', 'children'),
     Output('kpi-valor', 'children')],
    [Input('grafico-mapa', 'clickData'),
     Input('grafico-barra-pop', 'clickData'),
     Input('btn-limpar', 'n_clicks')]
)
def atualizar_dashboard(click_mapa, click_barra, btn_limpar):
    dff = df_sus.copy()
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    if trigger == 'btn-limpar':
        click_mapa = None
        click_barra = None

    if trigger == 'grafico-barra-pop' and click_barra:
        faixa_selecionada = click_barra['points'][0]['y']
        dff = dff[dff[pop_col] == faixa_selecionada]
    elif trigger == 'grafico-mapa' and click_mapa:
        regiao_selecionada = click_mapa['points'][0]['customdata'][0]
        dff = dff[dff['Regiao_Nome'] == regiao_selecionada]

    soma_qtd = dff['QTD_Total'].sum()
    soma_valor = dff['VL_Total'].sum()
    kpi_qtd_texto = f"{soma_qtd / 1_000_000:.0f} mi" if soma_qtd >= 1_000_000 else f"{soma_qtd:,.0f}".replace(',', '.')
    kpi_valor_texto = f"R$ {soma_valor / 1_000_000_000:.1f} bi" if soma_valor >= 1_000_000_000 else f"R$ {soma_valor / 1_000_000:.1f} mi".replace('.', ',')

    df_mapa = dff.groupby(['Nome_Municipio', 'Regiao_Nome', uf_col], as_index=False).agg({'VL_Total': 'sum', 'QTD_Total': 'sum', 'LATITUDE': 'first', 'LONGITUDE': 'first'})
    df_mapa = df_mapa[(df_mapa['VL_Total'] > 0) & (df_mapa['LATITUDE'] != 0)]
    df_mapa['QTD_BR'] = df_mapa['QTD_Total'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    df_mapa['VL_BR'] = df_mapa['VL_Total'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

    fig_mapa = px.scatter_mapbox(
        df_mapa, lat='LATITUDE', lon='LONGITUDE', size='VL_Total', color='Regiao_Nome',
        hover_name='Nome_Municipio', custom_data=['Regiao_Nome', 'QTD_BR', 'VL_BR', uf_col],
        mapbox_style='open-street-map', zoom=3.5, center={"lat": -15.78, "lon": -47.92},
        title='<b>Procedimentos por Município (Tamanho do círculo = Valor total gasto)</b>', size_max=40, template='plotly_white'
    )
    fig_mapa.update_traces(
        marker=dict(sizemin=4, opacity=0.75),
        hovertemplate="<b>Município:</b> %{hovertext}<br><b>Estado:</b> %{customdata[3]}<br><b>Região:</b> %{customdata[0]}<br><b>Qtd:</b> %{customdata[1]}<br><b>Valor Total:</b> R$ %{customdata[2]}<br><extra></extra>"
    )
    fig_mapa.update_layout(margin={'r': 0, 't': 40, 'l': 0, 'b': 0}, title_font_color='#2d3748', legend_title_text='Região')

    df_barra = dff.groupby(pop_col, as_index=False).agg({'QTD_Total': 'sum'})
    df_barra = df_barra.sort_values(by='QTD_Total', ascending=True)
    
    fig_barra = px.bar(
        df_barra, x='QTD_Total', y=pop_col, orientation='h',
        title='<b>Procedimentos por Faixa Populacional</b>',
        template='plotly_white', color_discrete_sequence=['#38a169']
    )
    fig_barra.update_layout(margin={'r': 0, 't': 40, 'l': 0, 'b': 0}, xaxis_title="Quantidade Total", yaxis_title=None, title_font_color='#2d3748')

    df_uf = dff.groupby(uf_col, as_index=False).agg({'QTD_Total': 'sum', 'VL_Total': 'sum'})
    df_uf['Valor_Medio'] = df_uf['VL_Total'] / df_uf['QTD_Total']
    df_uf['Valor_Medio'] = df_uf['Valor_Medio'].fillna(0)

    total_qtd = df_uf['QTD_Total'].sum()
    total_vl = df_uf['VL_Total'].sum()
    total_medio = total_vl / total_qtd if total_qtd > 0 else 0

    df_total = pd.DataFrame({uf_col: ['Total'], 'QTD_Total': [total_qtd], 'VL_Total': [total_vl], 'Valor_Medio': [total_medio]})
    df_final = pd.concat([df_total, df_uf.sort_values(by='VL_Total', ascending=False)], ignore_index=True)

    df_final['QTD_BR'] = df_final['QTD_Total'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    df_final['VL_BR'] = df_final['VL_Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_final['VM_BR'] = df_final['Valor_Medio'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    dados_tabela = df_final.to_dict('records')

    return fig_mapa, fig_barra, dados_tabela, kpi_qtd_texto, kpi_valor_texto


if __name__ == '__main__':
    app.run(debug=True, port=8052)
