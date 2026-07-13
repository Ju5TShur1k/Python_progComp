"""
Обработчики событий (callbacks) - Железнодорожная тематика
"""

import base64
import io
import time
import pandas as pd
import numpy as np
import dash
from dash import html, dash_table, Input, Output, State
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px

from modules import QualityEvaluator, TransportOptimizer
from config import SAMPLE_TRAINS, CHARACTERISTICS, DEPOT_NAMES, ROUTE_NAMES, USER_TRAINS


def register_callbacks(app, forecast_model):
    """Регистрация всех callbacks"""
    
    # ============================================================
    # CALLBACK ДЛЯ ДОБАВЛЕНИЯ ОБРАЗЦА (РУЧНОЙ ВВОД)
    # ============================================================
    
    @app.callback(
        Output("add-train-message", "children"),
        Input("btn-add-train", "n_clicks"),
        [State("train-type-select", "value"),
         State("new-train-name", "value"),
         State("new-train-speed", "value"),
         State("new-train-resource", "value"),
         State("new-train-power", "value"),
         State("new-train-reliability", "value"),
         State("new-train-comfort", "value"),
         State("new-train-fuel", "value")]
    )
    def add_train_manual(n_clicks, train_type, name, speed, resource, power, reliability, comfort, fuel):
        """Ручное добавление нового образца подвижного состава"""
        if not n_clicks:
            return ""
        
        if not name:
            return html.Div("❌ Ошибка: введите название модели", style={'color': 'red'})
        
        if not all([speed, resource, power, reliability, comfort]):
            return html.Div("❌ Ошибка: заполните все обязательные показатели", style={'color': 'red'})
        
        new_train = {
            "name": name,
            "max_speed": float(speed),
            "resource": float(resource),
            "traction_power": float(power),
            "reliability": float(reliability),
            "comfort": float(comfort),
            "fuel_consumption": float(fuel) if fuel and float(fuel) > 0 else 0
        }
        
        USER_TRAINS[train_type].append(new_train)
        
        return html.Div(f"✅ Образец '{name}' успешно добавлен! Нажмите 'Рассчитать' для обновления графиков.", 
                       style={'color': 'green', 'marginTop': '10px'})
    
    # ============================================================
    # CALLBACK ДЛЯ ОЦЕНКИ КАЧЕСТВА
    # ============================================================
    
    @app.callback(
        [Output("radar-chart", "figure"),
         Output("bar-chart", "figure"),
         Output("quality-results-text", "children")],
        [Input("btn-calc-quality", "n_clicks"),
         Input("upload-quality-data", "contents")],
        [State("train-type-select", "value"),
         State("upload-quality-data", "filename")]
    )
    def update_quality(n_clicks, contents, train_type, filename):
        """Обновление качества с учётом загруженных файлов и добавленных образцов"""
        
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        
        if "upload-quality-data" in trigger_id and contents:
            try:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                new_trains = df.to_dict('records')
                USER_TRAINS[train_type].extend(new_trains)
                print(f"✅ Загружено {len(new_trains)} образцов из файла {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки файла: {e}")
        
        if train_type is None:
            train_type = "Пассажирские электровозы"
        
        trains = SAMPLE_TRAINS.get(train_type, []) + USER_TRAINS.get(train_type, [])
        characteristics = CHARACTERISTICS.get(train_type, {})
        etalon = characteristics.get("etalon", {})
        stimulators = characteristics.get("stimulators", [])
        destimulators = characteristics.get("destimulators", [])
        labels = characteristics.get("labels", {})
        
        if not trains:
            empty_fig = go.Figure()
            empty_fig.update_layout(title="Нет данных для отображения. Добавьте образцы.")
            return empty_fig, empty_fig, html.Div("Нет образцов для оценки. Добавьте образцы через форму или загрузите CSV-файл.")
        
        results = []
        for train in trains:
            quality = QualityEvaluator.calculate_quality(train, etalon, stimulators, destimulators)
            results.append({"name": train["name"], "quality": quality, "data": train})
        
        results.sort(key=lambda x: x["quality"], reverse=True)
        
        # Радиальная диаграмма
        radar_fig = go.Figure()
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        
        for idx, result in enumerate(results):
            normalized = QualityEvaluator.get_normalized_values(
                result["data"], etalon, stimulators, destimulators
            )
            
            radar_fig.add_trace(go.Scatterpolar(
                r=[normalized.get(p, 0) for p in stimulators + destimulators],
                theta=[labels.get(p, p) for p in stimulators + destimulators],
                fill='toself' if idx == 0 else None,
                name=result["name"],
                line=dict(color=colors[idx % len(colors)], width=2),
                opacity=0.8
            ))
        
        radar_fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True, 
                    range=[0, 1.5],
                    tickvals=[0, 0.5, 1.0, 1.5],
                    ticktext=['0', '0,5', '1,0 (эталон)', '1,5']
                )
            ),
            title=f"Сравнение нормированных показателей ({train_type})",
            showlegend=True,
            legend=dict(x=1.1, y=1.0)
        )
        
        # Столбчатая диаграмма
        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(
            x=[r["name"] for r in results],
            y=[r["quality"] for r in results],
            marker_color=['#27ae60' if i == 0 else '#3498db' for i in range(len(results))],
            text=[f"{r['quality']:.1f}%" for r in results],
            textposition='auto'
        ))
        bar_fig.update_layout(
            title="Технический уровень подвижного состава",
            xaxis_title="Модель",
            yaxis_title="Технический уровень (%)",
            yaxis_range=[0, 120]
        )
        
        results_text = html.Div([
            html.H5(f"Результаты оценки для: {train_type}"),
            html.H6("Эталонный образец:"),
            html.P(", ".join([f"{labels.get(k,k)}: {v}" for k,v in etalon.items()])),
            html.H6("Рейтинг образцов:"),
            html.Ol([html.Li(f"{r['name']}: {r['quality']:.1f}%") for r in results])
        ])
        
        return radar_fig, bar_fig, results_text
    
    
    # ============================================================
    # CALLBACK ДЛЯ ПРОГНОЗА
    # ============================================================
    
    @app.callback(
    Output("prediction-result", "children"),
    Input("btn-predict", "n_clicks"),
    [State("pred-ticket", "value"),
     State("pred-route", "value"),
     State("pred-weekend", "value"),
     State("pred-trains", "value"),
     State("pred-season", "value")]
    )
    def update_prediction(n_clicks, ticket, route, weekend, trains, season):
        if not n_clicks:
            return html.Div("Введите значения и нажмите 'Получить прогноз'")
        
        try:
            prediction = forecast_model.predict({
                'ticket_price': ticket or 850,
                'route_length': route or 200,
                'is_weekend': weekend or 0,
                'trains_per_day': trains or 15,
                'season': season or 1
            })
            return html.Div([
                f"🚆 Прогноз пассажиропотока: {prediction:.0f} тыс. чел."
            ])
        except Exception as e:
            return html.Div(f"Ошибка: {str(e)}", style={'color': 'red'})
    
    # ============================================================
    # CALLBACK ДЛЯ ГРАФИКА ЗАВИСИМОСТИ
    # ============================================================
    
    @app.callback(
        Output("dependence-graph", "figure"),
        Input("btn-plot-dependence", "n_clicks"),
        [State("varying-feature", "value"),
         State("range-start", "value"),
         State("range-end", "value")]
    )
    def plot_dependence(n_clicks, varying_feature, range_start, range_end):
        if not n_clicks:
            return go.Figure().update_layout(title="Нажмите 'Построить график'")
        
        if range_start is None or range_end is None or range_start >= range_end:
            return go.Figure().update_layout(title="Укажите корректный диапазон")
        
        fixed = {
            'fuel_price': 50,
            'avg_route_length': 25,
            'is_holiday': 0,
            'bus_count': 30,
            'weather_condition': 1
        }
        
        range_values = np.linspace(range_start, range_end, 50)
        predictions = forecast_model.get_dependence(fixed, varying_feature, range_values)
        
        feature_names = {
            'fuel_price': 'Цена топлива (руб./л)',
            'avg_route_length': 'Протяжённость маршрута (км)',
            'bus_count': 'Количество поездов'
        }
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=range_values,
            y=predictions,
            mode='lines+markers',
            name='Выручка',
            line=dict(color='#3498db', width=3)
        ))
        
        fig.update_layout(
            title=f"Зависимость выручки от {feature_names.get(varying_feature, varying_feature)}",
            xaxis_title=feature_names.get(varying_feature, varying_feature),
            yaxis_title="Выручка (тыс. руб.)",
            template="plotly_white"
        )
        
        return fig
    
    # ============================================================
    # CALLBACK ДЛЯ ОПТИМИЗАЦИИ
    # ============================================================
    
    @app.callback(
        Output("optimization-results", "children"),
        Input("btn-optimize", "n_clicks"),
        [State(f"supply_{i}", "value") for i in range(3)] +
        [State(f"demand_{i}", "value") for i in range(5)] +
        [State("cost-matrix-table", "data")]
    )
    def solve_optimization(n_clicks, s0, s1, s2, d0, d1, d2, d3, d4, cost_data):
        if not n_clicks:
            return html.Div("Нажмите 'Оптимизировать' для расчёта оптимального распределения локомотивов")
        
        supply = [s0 or 0, s1 or 0, s2 or 0]
        demand = [d0 or 0, d1 or 0, d2 or 0, d3 or 0, d4 or 0]
        
        if sum(supply) == 0 or sum(demand) == 0:
            return html.Div("⚠️ Ошибка: суммы запасов и потребностей должны быть больше 0", 
                           style={'color': 'red', 'padding': '15px', 'backgroundColor': '#fee', 'borderRadius': '5px'})
        
        if cost_data:
            cost_matrix = np.array([[row[f"col_{j}"] for j in range(5)] for row in cost_data])
        else:
            cost_matrix = np.array([
                [500, 550, 600, 650, 700],
                [580, 520, 570, 620, 670],
                [650, 600, 550, 600, 650]
            ])
        
        total_supply = sum(supply)
        total_demand = sum(demand)
        
        if total_supply != total_demand:
            balance_msg = html.Div([
                html.P(f"⚠️ Задача НЕ сбалансирована:", style={'color': '#e67e22', 'fontWeight': 'bold'}),
                html.P(f"   Сумма запасов: {total_supply} локомотивов"),
                html.P(f"   Сумма потребностей: {total_demand} локомотивов"),
                html.P("   Будет добавлен фиктивный поставщик/потребитель с нулевыми затратами.")
            ])
        else:
            balance_msg = html.Div([
                html.P(f"✅ Задача сбалансирована: {total_supply} локомотивов", 
                       style={'color': '#27ae60', 'fontWeight': 'bold'})
            ])
        
        # Сравнение методов
        methods_to_test = ['highs', 'highs-ds', 'highs-ipm']
        method_names = {
            'highs': 'HiGHS (симплекс)',
            'highs-ds': 'HiGHS (двойной симплекс)',
            'highs-ipm': 'HiGHS (внутренней точки)'
        }
        
        results_by_method = []
        for method in methods_to_test:
            start_time = time.time()
            result = TransportOptimizer.solve_transport_problem_with_method(cost_matrix, supply, demand, method)
            end_time = time.time()
            elapsed_time = (end_time - start_time) * 1000
            results_by_method.append({
                'method_name': method_names.get(method, method),
                'success': result['success'],
                'total_cost': result.get('total_cost', None),
                'time_ms': elapsed_time
            })
        
        successful_results = [r for r in results_by_method if r['success']]
        
        if not successful_results:
            return html.Div("❌ Ошибка: ни один метод не нашёл решение", 
                           style={'color': 'red', 'padding': '15px', 'backgroundColor': '#fee', 'borderRadius': '5px'})
        
        best_result = min(successful_results, key=lambda x: x['total_cost'])
        
        selected_method = None
        for method in methods_to_test:
            if method_names[method] == best_result['method_name']:
                selected_method = method
                break
        
        final_result = TransportOptimizer.solve_transport_problem_with_method(
            cost_matrix, supply, demand, selected_method
        )
        solution = final_result['solution']
        total_cost = final_result['total_cost']
        n_supply = final_result['n_supply']
        n_demand = final_result['n_demand']
        
        # Таблица сравнения методов
        comparison_table = html.Div([
            html.H5("⏱️ Сравнение методов оптимизации", style={'marginTop': '15px'}),
            dash_table.DataTable(
                columns=[
                    {"name": "Метод", "id": "method"},
                    {"name": "Статус", "id": "status"},
                    {"name": "Затраты (руб.)", "id": "cost"},
                    {"name": "Время (мс)", "id": "time_ms"}
                ],
                data=[
                    {
                        "method": r['method_name'],
                        "status": "✅ Успешно" if r['success'] else "❌ Ошибка",
                        "cost": f"{r['total_cost']:,.0f}" if r['success'] else "-",
                        "time_ms": f"{r['time_ms']:.3f}"
                    }
                    for r in results_by_method
                ],
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'center'},
                style_header={'backgroundColor': '#34495e', 'color': 'white'}
            )
        ])
        
        depot_names = DEPOT_NAMES + ["Фиктивное депо"] if n_supply > 3 else DEPOT_NAMES[:n_supply]
        route_names = ROUTE_NAMES + ["Фиктивное направление"] if n_demand > 5 else ROUTE_NAMES[:n_demand]
        
        table_data = []
        for i in range(n_supply):
            row = {"Депо": depot_names[i]}
            for j in range(n_demand):
                row[route_names[j]] = f"{solution[i][j]:.0f}"
            table_data.append(row)
        
        table = dash_table.DataTable(
            columns=[{"name": "Депо / Направление", "id": "Депо"}] + 
                    [{"name": r, "id": r} for r in route_names],
            data=table_data,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'minWidth': '80px'},
            style_header={'backgroundColor': '#e67e22', 'color': 'white', 'fontWeight': 'bold'}
        )
        
        return html.Div([
            html.H5(f"💰 Минимальные затраты: {total_cost:,.0f} руб./км", 
                   style={'color': '#27ae60', 'fontSize': '18px'}),
            balance_msg,
            comparison_table,
            html.H6("Оптимальное распределение локомотивов:", style={'marginTop': '15px'}),
            table
        ])
    
    # ============================================================
    # CALLBACK ДЛЯ ТЕПЛОВОЙ КАРТЫ
    # ============================================================
    
    @app.callback(
        Output("cost-heatmap", "figure"),
        Input("btn-optimize", "n_clicks"),
        [State("cost-matrix-table", "data")]
    )
    def update_heatmap(n_clicks, cost_data):
        if cost_data and len(cost_data) > 0:
            try:
                cost_matrix = np.array([[row[f"col_{j}"] for j in range(5)] for row in cost_data])
            except:
                cost_matrix = np.array([
                    [500, 550, 600, 650, 700],
                    [580, 520, 570, 620, 670],
                    [650, 600, 550, 600, 650]
                ])
        else:
            cost_matrix = np.array([
                [500, 550, 600, 650, 700],
                [580, 520, 570, 620, 670],
                [650, 600, 550, 600, 650]
            ])
        
        fig = px.imshow(
            cost_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdYlGn_r',
            labels=dict(x="Направление", y="Депо", color="Затраты (руб./км)"),
            x=ROUTE_NAMES,
            y=DEPOT_NAMES
        )
        
        fig.update_layout(
            title="Тепловая карта матрицы затрат (руб./км)",
            xaxis_title="Направление",
            yaxis_title="Депо",
            width=600,
            height=400
        )
        
        return fig