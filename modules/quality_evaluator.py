"""
Модуль оценки технического уровня подвижного состава (ЖД)
"""

import numpy as np


class QualityEvaluator:
    """Класс для оценки технического уровня локомотивов и поездов"""
    
    @staticmethod
    def calculate_quality(sample, etalon, stimulators, destimulators):
        """Расчет комплексного показателя качества"""
        ratios = []
        for p in stimulators:
            if p in sample and p in etalon:
                ratios.append(sample[p] / etalon[p])
        for p in destimulators:
            if p in sample and p in etalon:
                ratios.append(etalon[p] / sample[p])
        
        if not ratios:
            return 0
        
        geom_mean = np.exp(np.mean(np.log(ratios)))
        return geom_mean * 100
    
    @staticmethod
    def get_normalized_values(sample, etalon, stimulators, destimulators):
        """Получение нормированных значений для радиальной диаграммы"""
        normalized = {}
        for p in stimulators:
            if p in sample and p in etalon:
                normalized[p] = sample[p] / etalon[p]
        for p in destimulators:
            if p in sample and p in etalon:
                normalized[p] = etalon[p] / sample[p]
        return normalized