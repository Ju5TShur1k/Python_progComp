"""
Конфигурационный файл для ИАС Железнодорожного перевозчика
"""

# ============================================================
# ССЫЛКА НА ДАННЫЕ
# ============================================================

GITHUB_CSV_URL = "https://raw.githubusercontent.com/Ju5TShur1k/Python_progComp/refs/heads/main/Passenger.csv"

# ============================================================
# ДАННЫЕ ДЛЯ ТРАНСПОРТНОЙ ЗАДАЧИ (ЖЕЛЕЗНОДОРОЖНАЯ ТЕМАТИКА)
# ============================================================

# Депо (поставщики локомотивов)
DEPOT_NAMES = ['Депо ТЧ-1', 'Депо ТЧ-2', 'Депо ТЧ-3']
SUPPLY = [30, 25, 20]  # Количество локомотивов в депо

# Направления (потребители локомотивов)
ROUTE_NAMES = ['Направление Москва-СПб', 'Направление Москва-Казань', 
               'Направление Москва-Екатеринбург', 'Направление Москва-Новосибирск', 
               'Направление Москва-Владивосток']
DEMAND = [15, 12, 18, 14, 16]  # Потребность в локомотивах на направлениях

# Матрица затрат на обслуживание локомотива (руб./км)
# Строки — депо, столбцы — направления
COST_MATRIX = [
    [500, 550, 600, 650, 700],  # ТЧ-1
    [580, 520, 570, 620, 670],  # ТЧ-2
    [650, 600, 550, 600, 650]   # ТЧ-3
]

# ============================================================
# ОБРАЗЦЫ ПОДВИЖНОГО СОСТАВА (ЖЕЛЕЗНОДОРОЖНАЯ ТЕМАТИКА)
# ============================================================

SAMPLE_TRAINS = {
    "Пассажирские электровозы": [
        {"name": "ЭП20", "max_speed": 200, "capacity": 0, "resource": 1200, 
         "comfort": 9.0, "fuel_consumption": 0, "traction_power": 8000, "reliability": 9.5},
        {"name": "2ЭС6", "max_speed": 120, "capacity": 0, "resource": 1500, 
         "comfort": 8.0, "fuel_consumption": 0, "traction_power": 9600, "reliability": 9.2},
        {"name": "ВЛ85", "max_speed": 110, "capacity": 0, "resource": 1800, 
         "comfort": 7.5, "fuel_consumption": 0, "traction_power": 10000, "reliability": 9.0},
    ],
    "Грузовые тепловозы": [
        {"name": "2ТЭ25К", "max_speed": 100, "capacity": 0, "resource": 1000, 
         "comfort": 7.0, "fuel_consumption": 180, "traction_power": 5000, "reliability": 8.5},
        {"name": "ТЭМ18", "max_speed": 80, "capacity": 0, "resource": 900, 
         "comfort": 6.5, "fuel_consumption": 160, "traction_power": 4000, "reliability": 8.0},
        {"name": "2М62", "max_speed": 90, "capacity": 0, "resource": 1100, 
         "comfort": 6.8, "fuel_consumption": 200, "traction_power": 4500, "reliability": 8.2},
    ],
    "Электропоезда (пригородные)": [
        {"name": "ЭД4М", "max_speed": 120, "capacity": 1200, "resource": 800, 
         "comfort": 8.0, "fuel_consumption": 0, "traction_power": 4000, "reliability": 9.0},
        {"name": "ЭГ2Тв", "max_speed": 130, "capacity": 1100, "resource": 700, 
         "comfort": 8.5, "fuel_consumption": 0, "traction_power": 4500, "reliability": 9.2},
        {"name": "Ласточка", "max_speed": 160, "capacity": 800, "resource": 900, 
         "comfort": 9.0, "fuel_consumption": 0, "traction_power": 5000, "reliability": 9.5},
    ]
}

# ============================================================
# ХАРАКТЕРИСТИКИ ДЛЯ ОЦЕНКИ КАЧЕСТВА (ЖЕЛЕЗНОДОРОЖНАЯ ТЕМАТИКА)
# ============================================================

CHARACTERISTICS = {
    "Пассажирские электровозы": {
        "stimulators": ["max_speed", "resource", "comfort", "traction_power", "reliability"],
        "destimulators": [],
        "labels": {
            "max_speed": "Макс. скорость (км/ч)",
            "resource": "Ресурс (тыс. км)",
            "comfort": "Комфорт (баллы)",
            "traction_power": "Мощность (кВт)",
            "reliability": "Надёжность (баллы)"
        },
        "etalon": {"max_speed": 200, "resource": 1200, "comfort": 9.0, 
                  "traction_power": 8000, "reliability": 9.5}
    },
    "Грузовые тепловозы": {
        "stimulators": ["max_speed", "resource", "traction_power", "reliability"],
        "destimulators": ["fuel_consumption"],
        "labels": {
            "max_speed": "Макс. скорость (км/ч)",
            "resource": "Ресурс (тыс. км)",
            "fuel_consumption": "Расход топлива (л/100км)",
            "traction_power": "Мощность (кВт)",
            "reliability": "Надёжность (баллы)"
        },
        "etalon": {"max_speed": 100, "resource": 1000, "fuel_consumption": 180,
                  "traction_power": 5000, "reliability": 8.5}
    },
    "Электропоезда (пригородные)": {
        "stimulators": ["max_speed", "capacity", "resource", "comfort", "traction_power", "reliability"],
        "destimulators": [],
        "labels": {
            "max_speed": "Макс. скорость (км/ч)",
            "capacity": "Вместимость (чел)",
            "resource": "Ресурс (тыс. км)",
            "comfort": "Комфорт (баллы)",
            "traction_power": "Мощность (кВт)",
            "reliability": "Надёжность (баллы)"
        },
        "etalon": {"max_speed": 160, "capacity": 1200, "resource": 900, 
                  "comfort": 9.0, "traction_power": 5000, "reliability": 9.5}
    }
}

# ============================================================
# СТИЛИ ИНТЕРФЕЙСА
# ============================================================

TAB_STYLE = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '12px',
    'fontWeight': 'bold',
    'backgroundColor': '#34495e',
    'color': 'white'
}

TAB_SELECTED_STYLE = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#e67e22',
    'color': 'white',
    'padding': '12px',
    'fontWeight': 'bold'
}

APP_LAYOUT_STYLE = {
    'fontFamily': 'Arial, sans-serif',
    'margin': '0 auto',
    'maxWidth': '1400px'
}

CARD_STYLE = {
    'padding': '20px',
    'backgroundColor': '#ecf0f1',
    'borderRadius': '10px',
    'margin': '10px'
}

BUTTON_STYLES = {
    'primary': {
        'margin': '10px 0',
        'padding': '10px 20px',
        'backgroundColor': '#3498db',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    },
    'success': {
        'margin': '10px 0',
        'padding': '10px 20px',
        'backgroundColor': '#27ae60',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    },
    'warning': {
        'margin': '10px 0',
        'padding': '10px 20px',
        'backgroundColor': '#e67e22',
        'color': 'white',
        'border': 'none',
        'borderRadius': '5px',
        'cursor': 'pointer'
    }
}

# ============================================================
# ПОЛЬЗОВАТЕЛЬСКИЕ ОБРАЗЦЫ
# ============================================================

USER_TRAINS = {
    "Пассажирские электровозы": [],
    "Грузовые тепловозы": [],
    "Электропоезда (пригородные)": []
}