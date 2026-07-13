"""
Модуль для загрузки данных
"""

import requests
import pandas as pd
from io import StringIO
import os


class DataLoader:
    """Класс для загрузки данных"""
    
    @staticmethod
    def load_bus_data(url):
        """Загрузка данных с GitHub или из локального файла"""
        try:
            print(f"🔄 Попытка загрузки с GitHub: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            print(f"✅ Данные загружены с GitHub: {len(df)} записей")
            return df
        except Exception as e:
            print(f"⚠️ Ошибка загрузки с GitHub: {e}")
            print("🔄 Попытка загрузки локального файла...")
            
            local_files = ['Passenger.csv', 'data.csv']
            for filename in local_files:
                if os.path.exists(filename):
                    try:
                        df = pd.read_csv(filename)
                        print(f"✅ Данные загружены из локального файла {filename}: {len(df)} записей")
                        return df
                    except Exception as e2:
                        print(f"⚠️ Ошибка чтения {filename}: {e2}")
            
            print("❌ Не удалось загрузить данные.")
            return None