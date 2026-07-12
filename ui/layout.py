"""
Вёрстка интерфейса (Железнодорожная тематика)
"""

from dash import dcc, html, dash_table
from config import (
    TAB_STYLE, TAB_SELECTED_STYLE, APP_LAYOUT_STYLE, CARD_STYLE,
    BUTTON_STYLES, COST_MATRIX, DEPOT_NAMES, ROUTE_NAMES, 
    SUPPLY, DEMAND
)


def get_layout():
    """Главный layout приложения"""
    return html.Div([
        html.H1("🚆 Информационно-аналитическая система", 
                style={'textAlign': 'center', 'color': '#2c3e50', 'padding': '20px'}),
        html.H3("Железнодорожный перевозчик — управление качеством подвижного состава, прогнозирование выручки и оптимизация",
                style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),
        
        dcc.Tabs(id="main-tabs", value="tab-quality", children=[
            dcc.Tab(label="🚂 Оценка технического уровня", value="tab-quality",
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
            dcc.Tab(label="📈 Прогноз выручки", value="tab-forecast",
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
            dcc.Tab(label="🛤️ Оптимизация перевозок", value="tab-optimization",
                    style=TAB_STYLE, selected_style=TAB_SELECTED_STYLE),
        ]),
        
        html.Div(id="tabs-content"),
    ], style=APP_LAYOUT_STYLE)


def render_quality_tab():
    """Вкладка оценки качества подвижного состава"""
    return html.Div([
        html.Div([
            html.Div([
                html.H4("Выбор типа подвижного состава", style={'color': '#2c3e50'}),
                dcc.Dropdown(
                    id="train-type-select",
                    options=[
                        {"label": "🚂 Пассажирские электровозы", "value": "Пассажирские электровозы"},
                        {"label": "🛤️ Грузовые тепловозы", "value": "Грузовые тепловозы"},
                        {"label": "🚄 Электропоезда (пригородные)", "value": "Электропоезда (пригородные)"}
                    ],
                    value="Пассажирские электровозы",
                    style={'marginBottom': '20px'}
                ),
                
                # Блок добавления образца
                html.H4("Загрузка данных", style={'marginTop': '20px', 'color': '#2c3e50'}),
                dcc.Upload(
                    id="upload-quality-data",
                    children=html.Div([
                        "📁 Перетащите CSV-файл или ",
                        html.A("выберите файл")
                    ]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed',
                        'borderRadius': '5px', 'textAlign': 'center', 'margin': '10px 0'
                    },
                    multiple=False
                ),
                
                html.H4("Ручное добавление образца", style={'marginTop': '20px', 'color': '#2c3e50'}),
                html.Div([
                    html.Label("Название модели:"),
                    dcc.Input(id="new-train-name", type="text", placeholder="Введите название модели",
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Макс. скорость (км/ч):"),
                    dcc.Input(id="new-train-speed", type="number", placeholder="200",
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Ресурс (тыс. км):"),
                    dcc.Input(id="new-train-resource", type="number", placeholder="1200",
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Мощность (кВт):"),
                    dcc.Input(id="new-train-power", type="number", placeholder="8000",
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Надёжность (баллы):"),
                    dcc.Input(id="new-train-reliability", type="number", placeholder="9.5", step=0.1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Комфорт (баллы):"),
                    dcc.Input(id="new-train-comfort", type="number", placeholder="9.0", step=0.1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("Расход топлива (л/100км) [если есть]:"),
                    dcc.Input(id="new-train-fuel", type="number", placeholder="0",
                             style={'width': '100%', 'marginBottom': '10px'}),
                    
                    html.Button("➕ Добавить образец", id="btn-add-train",
                               style={'margin': '10px 0', 'padding': '10px 20px',
                                      'backgroundColor': '#9b59b6', 'color': 'white', 'border': 'none',
                                      'borderRadius': '5px', 'cursor': 'pointer'}),
                    html.Div(id="add-train-message", style={'marginTop': '10px', 'color': 'green'})
                ], style={'padding': '15px', 'backgroundColor': '#f9e79f', 'borderRadius': '10px'}),
                
                html.Hr(),
                html.Button("📊 Рассчитать технический уровень", id="btn-calc-quality",
                           style=BUTTON_STYLES['success']),
            ], className="six columns", style=CARD_STYLE),
            
            html.Div([
                html.H4("Результаты оценки", style={'color': '#2c3e50'}),
                html.Div(id="quality-results-text"),
            ], className="six columns", style=CARD_STYLE),
        ], className="row"),
        
        html.Div([
            html.Div([
                html.H4("📡 Сравнение нормированных показателей", style={'textAlign': 'center'}),
                dcc.Graph(id="radar-chart")
            ], className="six columns", style={'padding': '10px'}),
            
            html.Div([
                html.H4("📊 Технический уровень", style={'textAlign': 'center'}),
                dcc.Graph(id="bar-chart")
            ], className="six columns", style={'padding': '10px'}),
        ], className="row"),
    ])


def render_forecast_tab(df_bus):
    """Вкладка прогнозирования выручки"""
    return html.Div([
        html.Div([
            html.Div([
                html.H4("Информация о модели", style={'color': '#2c3e50'}),
                html.Div(id="model-info", style={'marginBottom': '20px', 'padding': '15px',
                                                  'backgroundColor': '#d5f5e3', 'borderRadius': '5px'}),
                
                html.H4("Ручной прогноз выручки", style={'marginTop': '20px', 'color': '#2c3e50'}),
                html.Div([
                    html.Label("💰 Цена топлива (руб./л):"),
                    dcc.Input(id="pred-fuel", type="number", value=50, step=0.5,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("🛤️ Протяжённость маршрута (км):"),
                    dcc.Input(id="pred-route", type="number", value=25, step=1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("📅 Праздник/выходной (1=да, 0=нет):"),
                    dcc.Input(id="pred-holiday", type="number", value=0, step=1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("🚂 Количество поездов:"),
                    dcc.Input(id="pred-trains", type="number", value=30, step=1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Label("☁️ Погода (1=хорошая, 0=плохая):"),
                    dcc.Input(id="pred-weather", type="number", value=1, step=1,
                             style={'width': '100%', 'marginBottom': '10px'}),
                    html.Button("📈 Получить прогноз", id="btn-predict",
                               style=BUTTON_STYLES['success']),
                    html.Div(id="prediction-result", style={'marginTop': '15px', 'fontSize': '20px',
                                                            'fontWeight': 'bold', 'color': '#2980b9'}),
                ], style={'padding': '15px', 'backgroundColor': '#f9e79f', 'borderRadius': '10px'}),
            ], className="six columns", style=CARD_STYLE),
            
            html.Div([
                html.H4("Анализ зависимости выручки", style={'color': '#2c3e50'}),
                html.Label("Выберите признак для анализа:"),
                dcc.Dropdown(
                    id="varying-feature",
                    options=[
                        {"label": "Цена топлива", "value": "fuel_price"},
                        {"label": "Протяжённость маршрута", "value": "avg_route_length"},
                        {"label": "Количество поездов", "value": "bus_count"}
                    ],
                    value="fuel_price",
                    style={'marginBottom': '10px'}
                ),
                html.Label("Диапазон значений:"),
                html.Div([
                    dcc.Input(id="range-start", type="number", value=40,
                             style={'width': '45%', 'marginRight': '5%'}),
                    dcc.Input(id="range-end", type="number", value=60,
                             style={'width': '45%'})
                ], style={'marginBottom': '10px'}),
                html.Button("📊 Построить график зависимости", id="btn-plot-dependence",
                           style={'margin': '10px 0', 'padding': '10px 20px',
                                  'backgroundColor': '#8e44ad', 'color': 'white', 
                                  'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'}),
                dcc.Graph(id="dependence-graph", style={'marginTop': '20px'})
            ], className="six columns", style=CARD_STYLE),
        ], className="row"),
        
        html.Div([
            html.H4("📋 Исходные данные (первые 20 записей)", style={'marginLeft': '10px'}),
            dash_table.DataTable(
                id="forecast-data-table",
                columns=[{"name": i, "id": i} for i in df_bus.columns],
                data=df_bus.head(20).to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'},
                page_size=10
            )
        ], style=CARD_STYLE)
    ])


def render_optimization_tab():
    """Вкладка оптимизации распределения локомотивов по направлениям"""
    
    return html.Div([
        html.Div([
            html.Div([
                html.H4("Параметры транспортной задачи", style={'color': '#2c3e50'}),
                html.P("Распределение локомотивов из депо по направлениям", 
                       style={'color': '#7f8c8d', 'marginBottom': '15px'}),
                
                html.H5("Матрица затрат (руб./км)", style={'marginTop': '10px'}),
                dash_table.DataTable(
                    id="cost-matrix-table",
                    columns=[{"name": r, "id": f"col_{i}"} for i, r in enumerate(ROUTE_NAMES)],
                    data=[{f"col_{j}": COST_MATRIX[i][j] for j in range(5)} 
                          for i in range(3)],
                    editable=True,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'center', 'minWidth': '100px'},
                    style_header={'backgroundColor': '#e67e22', 'color': 'white'}
                ),
                
                html.H5("Запасы локомотивов в депо (ед.)", style={'marginTop': '20px'}),
                html.Div([
                    html.Div([
                        html.Label(f"{DEPOT_NAMES[i]}:"), 
                        dcc.Input(id=f"supply_{i}", type="number", value=SUPPLY[i],
                                 style={'width': '100px', 'marginLeft': '10px', 'marginBottom': '10px'})
                    ]) for i in range(3)
                ]),
                
                html.H5("Потребность направлений в локомотивах (ед.)", style={'marginTop': '20px'}),
                html.Div([
                    html.Div([
                        html.Label(f"{ROUTE_NAMES[i]}:"), 
                        dcc.Input(id=f"demand_{i}", type="number", value=DEMAND[i],
                                 style={'width': '100px', 'marginLeft': '10px', 'marginBottom': '10px'})
                    ]) for i in range(5)
                ]),
                
                html.Button("🚀 Оптимизировать распределение", id="btn-optimize",
                           style={'margin': '20px 0', 'padding': '12px 25px',
                                  'backgroundColor': '#e67e22', 'color': 'white', 'border': 'none',
                                  'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px'}),
            ], className="six columns", style=CARD_STYLE),
            
            html.Div([
                html.H4("Результаты оптимизации", style={'color': '#2c3e50'}),
                html.Div(id="optimization-results"),
            ], className="six columns", style=CARD_STYLE),
        ], className="row"),
        
        # Тепловая карта
        html.Div([
            html.H4("🔥 Тепловая карта матрицы затрат", style={'textAlign': 'center', 'marginTop': '20px'}),
            dcc.Graph(id="cost-heatmap")
        ], style=CARD_STYLE),
    ])