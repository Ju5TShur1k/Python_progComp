"""
Обработчики событий (callbacks)
"""

import dash
from dash import html, dash_table, Input, Output, State
from dash.dependencies import Input, Output, State
import numpy as np
import plotly.graph_objs as go
import plotly.express as px

from modules import QualityEvaluator, TransportOptimizer
from config import SAMPLE_BUSES


def register_callbacks(app, forecast_model):
    """Регистрация всех callbacks"""
    
    # ============================================================
    # CALLBACK ДЛЯ ОЦЕНКИ КАЧЕСТВА
    # ============================================================
    
    @app.callback(
        [Output("radar-chart", "figure"),
         Output("bar-chart", "figure"),
         Output("quality-results-text", "children")],
        [Input("btn-calc-quality", "n_clicks")],
        [State("bus-type-select", "value")]
    )
    def update_quality(n_clicks, bus_type):
        if bus_type is None:
            bus_type = "Междугородние автобусы"
        
        buses = SAMPLE_BUSES.get(bus_type, [])
        characteristics = QualityEvaluator.CHARACTERISTICS.get(bus_type, {})
        etalon = characteristics.get("etalon", {})
        stimulators = characteristics.get("stimulators", [])
        destimulators = characteristics.get("destimulators", [])
        labels = characteristics.get("labels", {})
        
        results = []
        for bus in buses:
            quality = QualityEvaluator.calculate_quality(bus, etalon, stimulators, destimulators)
            results.append({"name": bus["name"], "quality": quality, "data": bus})
        
        results.sort(key=lambda x: x["quality"], reverse=True)
        
        # Радиальная диаграмма (все образцы)
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
            title=f"Сравнение нормированных показателей ({bus_type})",
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
            title="Технический уровень автобусов",
            xaxis_title="Модель автобуса",
            yaxis_title="Технический уровень (%)",
            yaxis_range=[0, 120]
        )
        
        results_text = html.Div([
            html.H5(f"Результаты оценки для: {bus_type}"),
            html.H6("Эталонный образец:"),
            html.P(", ".join([f"{labels.get(k,k)}: {v}" for k,v in etalon.items()])),
            html.H6("Рейтинг образцов:"),
            html.Ol([html.Li(f"{r['name']}: {r['quality']:.1f}%") for r in results])
        ])
        
        return radar_fig, bar_fig, results_text
    
    # ============================================================
    # CALLBACK ДЛЯ ИНФОРМАЦИИ О МОДЕЛИ (ПОЛИНОМИАЛЬНАЯ)
    # ============================================================
    
    @app.callback(
        Output("model-info", "children"),
        Input("btn-predict", "n_clicks"),
        prevent_initial_call=False
    )
    def display_model_info(n_clicks):
        """Отображение информации о полиномиальной модели"""
        return html.Div([
            html.H5("📈 Полиномиальная регрессия (степень 2)", style={'marginBottom': '10px', 'color': '#2980b9'}),
            html.P("🔍 Модель учитывает нелинейные зависимости и взаимодействия признаков", 
                   style={'fontSize': '14px'}),
            html.P(f"📊 R² (качество модели): **{forecast_model.r2:.4f}**", style={'marginBottom': '5px'}),
            html.P(f"📉 MAE (средняя ошибка): **{forecast_model.mae:.2f}** тыс. руб.", style={'marginBottom': '5px'}),
            html.P(f"🔧 Степень полинома: **{forecast_model.degree}**", style={'marginBottom': '5px'}),
            html.P("📐 Модель учитывает: линейные эффекты, квадратичные эффекты и взаимодействия признаков",
                   style={'fontSize': '12px', 'color': '#7f8c8d', 'marginTop': '10px'})
        ])
    
    # ============================================================
    # CALLBACK ДЛЯ ПРОГНОЗА
    # ============================================================
    
    @app.callback(
        Output("prediction-result", "children"),
        Input("btn-predict", "n_clicks"),
        [State("pred-fuel", "value"),
         State("pred-route", "value"),
         State("pred-holiday", "value"),
         State("pred-buses", "value"),
         State("pred-weather", "value")]
    )
    def update_prediction(n_clicks, fuel, route, holiday, buses, weather):
        """Получение прогноза"""
        if not n_clicks:
            return html.Div("Введите значения и нажмите 'Получить прогноз'")
        
        try:
            prediction = forecast_model.predict({
                'fuel_price': fuel or 50,
                'avg_route_length': route or 25,
                'is_holiday': holiday or 0,
                'bus_count': buses or 30,
                'weather_condition': weather or 1
            })
            return html.Div([
                f"💰 Прогноз дневной выручки: {prediction:.0f} тыс. руб."
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
            'bus_count': 'Количество автобусов'
        }
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=range_values,
            y=predictions,
            mode='lines+markers',
            name='Дневная выручка',
            line=dict(color='#3498db', width=3)
        ))
        
        fig.update_layout(
            title=f"Зависимость выручки от {feature_names.get(varying_feature, varying_feature)}",
            xaxis_title=feature_names.get(varying_feature, varying_feature),
            yaxis_title="Дневная выручка (тыс. руб.)",
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
        """Решение транспортной задачи"""
        import time
        
        if not n_clicks:
            return html.Div("Нажмите 'Оптимизировать' для расчёта оптимального распределения автобусов")
        
        # Сбор данных о запасах (3 гаража)
        supply = [s0 or 0, s1 or 0, s2 or 0]
        
        # Сбор данных о потребностях (5 маршрутов)
        demand = [d0 or 0, d1 or 0, d2 or 0, d3 or 0, d4 or 0]
        
        # Проверка корректности данных
        if sum(supply) == 0 or sum(demand) == 0:
            return html.Div("⚠️ Ошибка: суммы запасов и потребностей должны быть больше 0", 
                           style={'color': 'red', 'padding': '15px', 'backgroundColor': '#fee', 'borderRadius': '5px'})
        
        # Формирование матрицы затрат из таблицы
        if cost_data:
            cost_matrix = np.array([[row[f"col_{j}"] for j in range(5)] for row in cost_data])
        else:
            cost_matrix = np.array([
                [500, 550, 600, 650, 700],
                [580, 520, 570, 620, 670],
                [650, 600, 550, 600, 650]
            ])
        
        # Проверка баланса задачи
        total_supply = sum(supply)
        total_demand = sum(demand)
        
        if total_supply != total_demand:
            balance_msg = html.Div([
                html.P(f"⚠️ Задача НЕ сбалансирована:", style={'color': '#e67e22', 'fontWeight': 'bold'}),
                html.P(f"   Сумма запасов: {total_supply} автобусов"),
                html.P(f"   Сумма потребностей: {total_demand} автобусов"),
                html.P("   Будет добавлен фиктивный поставщик/потребитель с нулевыми затратами.")
            ])
        else:
            balance_msg = html.Div([
                html.P(f"✅ Задача сбалансирована: {total_supply} автобусов", 
                       style={'color': '#27ae60', 'fontWeight': 'bold'})
            ])
        
        # Сравнение методов оптимизации
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
        
        # Выбираем лучший результат
        best_result = min(successful_results, key=lambda x: x['total_cost'])
        
        # Находим метод по имени
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
        
        # Названия (с учётом возможного добавления фиктивных)
        garage_names = ['Гараж G1', 'Гараж G2', 'Гараж G3']
        route_names = ['Маршрут M1', 'Маршрут M2', 'Маршрут M3', 'Маршрут M4', 'Маршрут M5']
        
        if n_supply > 3:
            garage_names = garage_names + ["Фиктивный гараж"]
        if n_demand > 5:
            route_names = route_names + ["Фиктивный маршрут"]
        
        # Формирование таблицы результатов
        table_data = []
        for i in range(n_supply):
            row = {"Гараж": garage_names[i]}
            for j in range(n_demand):
                row[route_names[j]] = f"{solution[i][j]:.0f}"
            table_data.append(row)
        
        table = dash_table.DataTable(
            columns=[{"name": "Гараж / Маршрут", "id": "Гараж"}] + 
                    [{"name": r, "id": r} for r in route_names],
            data=table_data,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'center', 'minWidth': '80px'},
            style_header={'backgroundColor': '#3498db', 'color': 'white', 'fontWeight': 'bold'}
        )
        
        return html.Div([
            html.H5(f"💰 Минимальные затраты: {total_cost:,.0f} руб./день", 
                   style={'color': '#27ae60', 'fontSize': '18px'}),
            balance_msg,
            comparison_table,
            html.H6("Оптимальное распределение автобусов:", style={'marginTop': '15px'}),
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
        """Тепловая карта матрицы затрат"""
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
            labels=dict(x="Маршрут", y="Гараж", color="Затраты (руб.)"),
            x=['M1', 'M2', 'M3', 'M4', 'M5'],
            y=['Гараж G1', 'Гараж G2', 'Гараж G3']
        )
        
        fig.update_layout(
            title="Тепловая карта матрицы затрат (руб./автобус в день)",
            xaxis_title="Маршрут",
            yaxis_title="Гараж",
            width=600,
            height=400
        )
        
        return fig