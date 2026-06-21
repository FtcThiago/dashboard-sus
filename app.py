import dash
from dash import dcc, html, Input, Output, dash_table, ctx
import plotly.express as px
import pandas as pd
import re

# Lendo a planilha do SUS direto para o pandas
df = pd.read_excel("C:\\Users\\thiag\\Downloads\\Vai apagar\\CIA014_SUS_Prova_2.xlsx")

# Aqui a gente checa se as coordenadas vieram como texto (com vírgula). 
# Se sim, trocamos a vírgula por ponto pro Python conseguir converter pra float e plotar no mapa.
if df['LATITUDE'].dtype == 'object':
    df['LATITUDE'] = df['LATITUDE'].str.replace(',', '.').astype(float)
if df['LONGITUDE'].dtype == 'object':
    df['LONGITUDE'] = df['LONGITUDE'].str.replace(',', '.').astype(float)

# Garantindo que células vazias fiquem como zero para não quebrar as somas depois
df['VL_Total'] = df['VL_Total'].fillna(0)
df['QTD_Total'] = df['QTD_Total'].fillna(0)

# Identificando as colunas automaticamente caso o nome varie um pouco
uf_col = 'UF_NOME' if 'UF_NOME' in df.columns else 'UF'
pop_col = 'Faixa_Populacao' if 'Faixa_Populacao' in df.columns else 'Faixa_populacao'

# --- Faxina nos textos (Removendo lixos e o 'X' isolado) ---
df['Nome_Municipio'] = df['Nome_Municipio'].astype(str)
df['Regiao_Nome'] = df['Regiao_Nome'].astype(str)

for col in ['Nome_Municipio', 'Regiao_Nome']:
    # Esse monte de .str.replace usa expressões regulares (Regex) para caçar padrões estranhos,
    # como códigos hexadecimais (ex: 0x250) ou letras 'X' que ficaram soltas no meio do texto.
    df[col] = df[col].str.replace(r'0?x[0-9a-fA-F]+', ' ', regex=True, case=False)
    df[col] = df[col].str.replace(r'[^a-zA-ZÀ-ÿ\s]', ' ', regex=True)
    df[col] = df[col].str.replace(r'\b[xX]\b', ' ', regex=True) 
    df[col] = df[col].str.replace(r'\s+', ' ', regex=True).str.strip().str.title()

def formatar_faixa_populacao(texto):
    # Deixa os textos das faixas populacionais bonitos e padronizados
    texto = str(texto).replace('_', ' ')
    texto = re.sub(r'0?x[0-9a-fA-F]+', ' ', texto, flags=re.IGNORECASE)
    texto = re.sub(r'\b[xX]\b', ' ', texto)
    # Esse lambda abaixo bota pontos de milhar em números puros (ex: 10000 vira 10.000)
    texto = re.sub(r'\b(\d{4,8})\b', lambda m: f"{int(m.group(1)):,}".replace(',', '.'), texto)
    texto = texto.lower().replace('ate', 'Até')
    partes = [p.capitalize() if p not in ['a', 'e', 'de'] else p for p in texto.split()]
    return " ".join(partes).capitalize().strip()

df[pop_col] = df[pop_col].apply(formatar_faixa_populacao)

# --- Configuração da estrutura visual do Dash ---
app = dash.Dash(__name__)
server = app.server # Linha crucial! O Render precisa dela para rodar o app em produção

# Um estilo padrão em formato de cartão com sombra leve para os gráficos
CARD_STYLE = {
    'backgroundColor': 'white', 'padding': '20px', 
    'borderRadius': '12px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.05)',
    'marginBottom': '20px'
}

app.layout = html.Div(style={'fontFamily': 'Segoe UI, Arial, sans-serif', 'padding': '30px', 'backgroundColor': '#f4f6f9', 'minHeight': '100vh'}, children=[
    
    # Topo do Dashboard
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '20px', 'borderBottom': '2px solid #e2e8f0', 'paddingBottom': '15px'}, children=[
        html.Div([
            html.H1("Dashboard SUS 2023", style={'color': '#1a202c', 'margin': '0', 'fontWeight': '700', 'fontSize': '28px'}),
            html.H4("Análise Estratégica de Municípios e Estados", style={'color': '#718096', 'margin': '5px 0 0 0', 'fontWeight': '400', 'fontSize': '15px'}),
        ]),
        html.Div([
            html.Span("Made by ", style={'color': '#718096'}),
            html.Span("Thiago Félix", style={'fontWeight': 'bold', 'color': '#2b6cb0'})
        ], style={'fontSize': '16px'})
    ]),

    # Resumo descritivo e o botão para resetar os cliques
    html.Div(style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'marginBottom': '20px'}, children=[
        html.P(
            "Verifica-se junto a amostra da base do SUS do Ano de 2023 um total de quatrocentos "
            "e quarenta milhões de procedimentos feitos em todo o Brasil, gerando um custo total "
            "de vinte e um Bilhões de reais investido para suprir tais procedimentos.",
            style={'fontSize': '16px', 'color': '#4a5568', 'maxWidth': '700px', 'lineHeight': '1.5', 'margin': '0'}
        ),
        html.Button(
            '🔄 Limpar Filtros Cruzados', id='btn-limpar', n_clicks=0, 
            style={'padding': '10px 20px', 'backgroundColor': '#2b6cb0', 'color': 'white', 'border': 'none', 'borderRadius': '8px', 'cursor': 'pointer', 'fontWeight': 'bold', 'boxShadow': '0 2px 4px rgba(43,108,176,0.3)'}
        )
    ]),

    # Blocos de Indicadores (KPIs) que mudam sozinhos com os filtros
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '25px'}, children=[
        html.Div(style={**CARD_STYLE, 'flex': '1', 'borderLeft': '5px solid #3182ce'}, children=[
            html.P("Quantidade Total de Procedimentos", style={'margin': '0', 'color': '#718096', 'fontSize': '14px', 'fontWeight': '600', 'textTransform': 'uppercase'}),
            html.H2(id='kpi-qtd', style={'margin': '10px 0 0 0', 'color': '#2d3748', 'fontSize': '32px'})
        ]),
        html.Div(style={**CARD_STYLE, 'flex': '1', 'borderLeft': '5px solid #38a169'}, children=[
            html.P("Valor Total dos Procedimentos", style={'margin': '0', 'color': '#718096', 'fontSize': '14px', 'fontWeight': '600', 'textTransform': 'uppercase'}),
            html.H2(id='kpi-valor', style={'margin': '10px 0 0 0', 'color': '#2d3748', 'fontSize': '32px'})
        ])
    ]),

    # Card do mapa ocupando a largura total da tela
    html.Div(style=CARD_STYLE, children=[
        dcc.Graph(id='grafico-mapa', style={'height': '55vh'})
    ]),
    
    # Parte de baixo dividida entre o gráfico de barras e a tabela real-time
    html.Div(style={'display': 'flex', 'flexDirection': 'row', 'gap': '20px'}, children=[
        
        html.Div(style={**CARD_STYLE, 'flex': '1'}, children=[
            dcc.Graph(id='grafico-barra-pop', style={'height': '45vh'})
        ]),
        
        html.Div(style={**CARD_STYLE, 'flex': '1.2'}, children=[
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
                style_header={'backgroundColor': '#ebf8ff', 'color': '#2b6cb0', 'fontWeight': 'bold', 'borderBottom': '2px solid #bee3f8'},
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f7fafc'},
                    # Deixa a linha com o texto "Total" em negrito e com fundo destacado
                    {'if': {'filter_query': '{'+uf_col+'} = "Total"'}, 'fontWeight': 'bold', 'backgroundColor': '#e2e8f0', 'color': '#1a202c'}
                ]
            )
        ])
    ])
])

# --- O motor de interatividade do Dashboard (Callback único) ---
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
    # Criamos uma cópia limpa dos dados para aplicar os filtros dinamicamente
    dff = df.copy()

    # O ctx.triggered serve para descobrir de onde veio a ação do usuário (qual gráfico ele clicou)
    trigger = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Se ele clicou no botão limpar, ignoramos os cliques anteriores e mostramos tudo de novo
    if trigger == 'btn-limpar':
        click_mapa = None
        click_barra = None

    # Lógica do Filtro Cruzado Interativo:
    # Se clicar na barra de população, filtra o mapa e a tabela por aquela faixa.
    # Se clicar em uma ponto no mapa, filtra os outros gráficos para aquela Região específica.
    if trigger == 'grafico-barra-pop' and click_barra:
        faixa_selecionada = click_barra['points'][0]['y']
        dff = dff[dff[pop_col] == faixa_selecionada]
    elif trigger == 'grafico-mapa' and click_mapa:
        regiao_selecionada = click_mapa['points'][0]['customdata'][0]
        dff = dff[dff['Regiao_Nome'] == regiao_selecionada]

    # Re-calculando os indicadores do topo com base no filtro atual
    soma_qtd = dff['QTD_Total'].sum()
    soma_valor = dff['VL_Total'].sum()
    kpi_qtd_texto = f"{soma_qtd / 1_000_000:.0f} mi" if soma_qtd >= 1_000_000 else f"{soma_qtd:,.0f}".replace(',', '.')
    kpi_valor_texto = f"R$ {soma_valor / 1_000_000_000:.1f} bi" if soma_valor >= 1_000_000_000 else f"R$ {soma_valor / 1_000_000:.1f} mi".replace('.', ',')

    # Montando o mapa atualizado
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

    # Montando o gráfico de barras atualizado
    df_barra = dff.groupby(pop_col, as_index=False).agg({'QTD_Total': 'sum'})
    df_barra = df_barra.sort_values(by='QTD_Total', ascending=True)
    
    fig_barra = px.bar(
        df_barra, x='QTD_Total', y=pop_col, orientation='h',
        title='<b>Procedimentos por Faixa Populacional</b>',
        template='plotly_white', color_discrete_sequence=['#3182ce']
    )
    fig_barra.update_layout(margin={'r': 0, 't': 40, 'l': 0, 'b': 0}, xaxis_title="Quantidade Total", yaxis_title=None, title_font_color='#2d3748')

    # Recalculando a tabela dinâmica (Com valor médio por procedimento e linha de totalizador geral)
    df_uf = dff.groupby(uf_col, as_index=False).agg({'QTD_Total': 'sum', 'VL_Total': 'sum'})
    df_uf['Valor_Medio'] = df_uf['VL_Total'] / df_uf['QTD_Total']
    df_uf['Valor_Medio'] = df_uf['Valor_Medio'].fillna(0)

    total_qtd = df_uf['QTD_Total'].sum()
    total_vl = df_uf['VL_Total'].sum()
    total_medio = total_vl / total_qtd if total_qtd > 0 else 0

    df_total = pd.DataFrame({uf_col: ['Total'], 'QTD_Total': [total_qtd], 'VL_Total': [total_vl], 'Valor_Medio': [total_medio]})
    df_final = pd.concat([df_total, df_uf.sort_values(by='VL_Total', ascending=False)], ignore_index=True)

    # Deixando a formatação numérica do jeito que o brasileiro gosta (pontos e vírgulas nos locais certos)
    df_final['QTD_BR'] = df_final['QTD_Total'].apply(lambda x: f"{x:,.0f}".replace(',', '.'))
    df_final['VL_BR'] = df_final['VL_Total'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    df_final['VM_BR'] = df_final['Valor_Medio'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    
    dados_tabela = df_final.to_dict('records')

    # Retorna todas as variáveis atualizadas para a interface do Dash colocar na tela
    return fig_mapa, fig_barra, dados_tabela, kpi_qtd_texto, kpi_valor_texto

if __name__ == '__main__':
    app.run(debug=True)