"""
Модуль прогнозирования дневной выручки (полиномиальная регрессия)
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split


class RevenueForecast:
    """Класс для прогнозирования дневной выручки (полиномиальная модель)"""
    
    def __init__(self, df):
        self.df = df
        self.model = None
        self.poly_features = None
        self.scaler = None
        self.is_polynomial = True  # Указываем, что используется полиномиальная модель
        self.test_size = 0.2
        self.random_state = 42
        self.degree = 2  # степень полинома
        self.poly_feature_names = None
        
        # Определение признаков и целевой переменной
        self.feature_names = ['fuel_price', 'avg_route_length', 'is_holiday', 
                              'bus_count', 'weather_condition']
        self.target_name = 'daily_revenue'
        
        # Разделение на обучающую и тестовую выборки
        self.X_train, self.X_test, self.y_train, self.y_test = self._split_data()
        
        # Описания признаков
        self.feature_labels = {
            'fuel_price': 'Цена топлива (руб./л)',
            'avg_route_length': 'Средняя протяжённость маршрута (км)',
            'is_holiday': 'Праздник/выходной (1=да, 0=нет)',
            'bus_count': 'Количество работающих автобусов',
            'weather_condition': 'Погода (1=хорошая, 0=плохая)'
        }
        
        # Автоматическое обучение полиномиальной модели
        self.train_polynomial()
    
    def _split_data(self):
        """Разделение данных на обучающую и тестовую выборки"""
        X = self.df[self.feature_names].values
        y = self.df[self.target_name].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, 
            test_size=self.test_size, 
            random_state=self.random_state,
            shuffle=True
        )
        
        print(f"📊 Разделение данных: обучение {len(X_train)} записей, тест {len(X_test)} записей")
        return X_train, X_test, y_train, y_test
    
    def train_polynomial(self, degree=2):
        """Обучение полиномиальной регрессии на трен данных"""
        self.degree = degree
        self.is_polynomial = True
        
        # Нормализация (важно для полиномов!)
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(self.X_train)
        X_test_scaled = self.scaler.transform(self.X_test)
        
        # Полиномиальные признаки
        self.poly_features = PolynomialFeatures(degree=degree, include_bias=False)
        X_train_poly = self.poly_features.fit_transform(X_train_scaled)
        X_test_poly = self.poly_features.transform(X_test_scaled)
        
        # Обучение
        self.model = LinearRegression()
        self.model.fit(X_train_poly, self.y_train)
        
        # Оценка на ТЕСТОВЫХ данных
        y_pred = self.model.predict(X_test_poly)
        self.r2 = r2_score(self.y_test, y_pred)
        self.mae = mean_absolute_error(self.y_test, y_pred)
        
        # Сохраняем информацию о признаках
        self.poly_feature_names = self.poly_features.get_feature_names_out(self.feature_names)
        
        print(f"📈 Полиномиальная модель (степень {degree}): R² = {self.r2:.4f}, MAE = {self.mae:.2f}")
        
        # Вывод наиболее важных коэффициентов
        self._print_important_coefficients()
        
        return self.model, self.r2, self.mae
    
    def _print_important_coefficients(self):
        """Вывод наиболее важных коэффициентов модели"""
        if self.poly_feature_names is None:
            return
            
        coef_df = pd.DataFrame({
            'Признак': self.poly_feature_names,
            'Коэффициент': self.model.coef_
        })
        coef_df['Абс'] = np.abs(coef_df['Коэффициент'])
        coef_df = coef_df.sort_values('Абс', ascending=False)
        
        print("\n📊 Топ-5 важнейших признаков полиномиальной модели:")
        for i, row in coef_df.head(5).iterrows():
            print(f"   {row['Признак']:30s} : {row['Коэффициент']:+.4f}")
        print()
    
    def predict(self, features_dict):
        """Прогноз для заданных признаков"""
        features_list = [features_dict[f] for f in self.feature_names]
        
        # Нормализация
        features_scaled = self.scaler.transform([features_list])
        
        # Полиномиальные признаки
        X_pred = self.poly_features.transform(features_scaled)
        
        return self.model.predict(X_pred)[0]
    
    def get_dependence(self, fixed_features, varying_feature, range_values):
        """Получение зависимости целевой переменной от изменяемого признака"""
        predictions = []
        for val in range_values:
            features = fixed_features.copy()
            features[varying_feature] = val
            predictions.append(self.predict(features))
        return predictions
    
    def get_feature_importance(self):
        """Получение важности признаков (по абсолютному значению коэффициентов)"""
        if self.model and self.poly_feature_names is not None:
            importance = {}
            for i, name in enumerate(self.poly_feature_names):
                if ' ' not in name and '^' not in name:  # только линейные признаки
                    importance[name] = self.model.coef_[i]
            return importance
        return None