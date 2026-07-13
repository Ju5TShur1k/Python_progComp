"""
Модуль прогнозирования пассажиропотока
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split


class PassengerForecast:
    def __init__(self, df):
        self.df = df
        self.model = None
        self.poly_features = None
        self.scaler = None
        self.is_polynomial = True
        self.test_size = 0.2
        self.random_state = 42
        self.degree = 2
        self.poly_feature_names = None
        
        # Признаки для Passenger.csv
        self.feature_names = [
            'ticket_price',
            'route_length',
            'is_weekend',
            'trains_per_day',
            'season'
        ]
        self.target_name = 'passengers'
        
        self.feature_labels = {
            'ticket_price': 'Цена билета (руб.)',
            'route_length': 'Протяжённость маршрута (км)',
            'is_weekend': 'Выходной/праздник (1=да, 0=нет)',
            'trains_per_day': 'Количество поездов в сутки',
            'season': 'Сезон (1-зима, 2-весна, 3-лето, 4-осень)'
        }
        
        self.X_train, self.X_test, self.y_train, self.y_test = self._split_data()
        self.train_polynomial()
    
    def _split_data(self):
        X = self.df[self.feature_names].values
        y = self.df[self.target_name].values
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, shuffle=True
        )
        print(f"📊 Разделение: обучение {len(X_train)}, тест {len(X_test)}")
        return X_train, X_test, y_train, y_test
    
    def train_polynomial(self, degree=2):
        self.degree = degree
        self.is_polynomial = True
        
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(self.X_train)
        X_test_scaled = self.scaler.transform(self.X_test)
        
        self.poly_features = PolynomialFeatures(degree=degree, include_bias=False)
        X_train_poly = self.poly_features.fit_transform(X_train_scaled)
        X_test_poly = self.poly_features.transform(X_test_scaled)
        
        self.model = LinearRegression()
        self.model.fit(X_train_poly, self.y_train)
        
        y_pred = self.model.predict(X_test_poly)
        self.r2 = r2_score(self.y_test, y_pred)
        self.mae = mean_absolute_error(self.y_test, y_pred)
        
        self.poly_feature_names = self.poly_features.get_feature_names_out(self.feature_names)
        print(f"📈 Полиномиальная модель: R² = {self.r2:.4f}, MAE = {self.mae:.2f}")
        return self.model, self.r2, self.mae
    
    def predict(self, features_dict):
        features_list = [features_dict[f] for f in self.feature_names]
        features_scaled = self.scaler.transform([features_list])
        X_pred = self.poly_features.transform(features_scaled)
        return self.model.predict(X_pred)[0]
    
    def get_dependence(self, fixed_features, varying_feature, range_values):
        predictions = []
        for val in range_values:
            features = fixed_features.copy()
            features[varying_feature] = val
            predictions.append(self.predict(features))
        return predictions