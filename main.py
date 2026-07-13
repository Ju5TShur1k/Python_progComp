"""
Информационно-аналитическая система для Железнодорожного перевозчика
"""

import warnings
import dash
from dash import html

from config import GITHUB_CSV_URL
from utils.data_loader import DataLoader
from modules.passenger_forecast import PassengerForecast
from ui.layout import get_layout, render_quality_tab, render_forecast_tab, render_optimization_tab
from ui.callbacks import register_callbacks

warnings.filterwarnings('ignore')

print("🔄 Загрузка данных с GitHub...")
df = DataLoader.load_bus_data(GITHUB_CSV_URL)
print(f"✅ Данные загружены: {len(df)} записей")

print("\n" + "=" * 50)
print("ОБУЧЕНИЕ МОДЕЛИ ПАССАЖИРОПОТОКА")
print("=" * 50)
forecast_model = PassengerForecast(df)
print("=" * 50 + "\n")

app = dash.Dash(__name__, title="ИАС Железнодорожный перевозчик")
app.config.suppress_callback_exceptions = True

app.layout = get_layout()
register_callbacks(app, forecast_model)

@app.callback(
    dash.dependencies.Output("tabs-content", "children"),
    dash.dependencies.Input("main-tabs", "value")
)
def render_content(tab):
    if tab == "tab-quality":
        return render_quality_tab()
    elif tab == "tab-forecast":
        return render_forecast_tab(df)
    elif tab == "tab-optimization":
        return render_optimization_tab()
    return html.Div()

if __name__ == "__main__":
    app.run(debug=True, port=8050)