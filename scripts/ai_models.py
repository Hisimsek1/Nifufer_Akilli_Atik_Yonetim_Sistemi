"""
Akıllı Atık Yönetim Sistemi - Yapay Zeka Model Uygulaması
Nilüfer Belediyesi

Bu modül aşağıdakileri içerir:
1. Doluluk Seviyesi Tahmin Modeli (AI Model #1)
2. Dinamik Rotalama & Filo Yönetimi (AI Model #2)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
import joblib
import json


# ============== MODEL #1: DOLULUK SEVİYESİ TAHMİNİ ==============

class FillLevelPredictor:
    """
    Atık konteynerinin dolu olup olmadığını tarihsel veriler
    ve çevresel faktörlere dayanarak tahmin eder.
    """
    
    def __init__(self):
        self.model = None
        self.model_version = "v1.0.0"
        self.feature_columns = [
            'hours_since_last_collection',
            'container_capacity',
            'population_density',
            'day_of_week',
            'is_weekend',
            'season',
            'avg_tonnage_last_month',
            'container_type_encoded',
            'historical_fill_rate'
        ]
    
    def prepare_features(self, data):
        """
        Ham veriden özellik mühendisliği
        
        Parametreler:
            data: Konteyner bilgilerini içeren DataFrame
            
        Döndürür:
            Oluşturulmuş özellikleri içeren DataFrame
        """
        features = pd.DataFrame()
        
        # Zaman bazlı özellikler
        data['last_collection_date'] = pd.to_datetime(data['last_collection_date'])
        current_time = datetime.now()
        
        features['hours_since_last_collection'] = (
            (current_time - data['last_collection_date']).dt.total_seconds() / 3600
        )
        
        features['day_of_week'] = current_time.weekday()
        features['is_weekend'] = (current_time.weekday() >= 5).astype(int)
        features['season'] = self._get_season(current_time)
        
        # Konteyner özellikleri
        features['container_capacity'] = data['capacity_liters']
        
        # Konteyner tipi kodlama (one-hot encoding alternatifi: basit etiket kodlama)
        container_type_map = {'plastic': 1, 'glass': 2, 'organic': 3, 'paper': 4}
        features['container_type_encoded'] = data['container_type'].map(container_type_map)
        
        # Nüfus yoğunluğu
        features['population_density'] = data['population_density']
        
        # Tarihsel desenler
        features['avg_tonnage_last_month'] = data['avg_tonnage_last_30_days']
        features['historical_fill_rate'] = data['historical_fill_rate']
        
        return features
    
    def _get_season(self, date):
        """Tarihten mevsim bilgisi al (0=Kış, 1=İlkbahar, 2=Yaz, 3=Sonbahar)"""
        month = date.month
        if month in [12, 1, 2]:
            return 0  # Kış
        elif month in [3, 4, 5]:
            return 1  # İlkbahar
        elif month in [6, 7, 8]:
            return 2  # Yaz
        else:
            return 3  # Sonbahar
    
    def train(self, training_data, target_column='is_full'):
        """
        Doluluk seviyesi tahmin modelini eğit
        
        Parametreler:
            training_data: Tarihsel konteyner verilerini içeren DataFrame
            target_column: Hedef değişkenin adı (ikili: 0=dolu değil, 1=dolu)
        """
        print("Eğitim özellikleri hazırlanıyor...")
        X = self.prepare_features(training_data)
        y = training_data[target_column]
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print("Random Forest modeli eğitiliyor...")
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Değerlendir
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n=== Model Eğitim Sonuçları ===")
        print(f"Doğruluk: {accuracy:.4f}")
        print("\nSınıflandırma Raporu:")
        print(classification_report(y_test, y_pred, target_names=['Dolu Değil', 'Dolu']))
        
        # Özellik önemi
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nEn Önemli 5 Özellik:")
        print(feature_importance.head())
        
        return accuracy
    
    def predict(self, container_data):
        """
        Tek bir konteyner için doluluk olasılığını tahmin et
        
        Parametreler:
            container_data: Konteyner bilgilerini içeren sözlük veya DataFrame
            
        Döndürür:
            Tahmin sonuçlarını içeren sözlük
        """
        if self.model is None:
            raise ValueError("Model henüz eğitilmedi. Önce train() metodunu çağırın.")
        
        # Sözlük ise DataFrame'e dönüştür
        if isinstance(container_data, dict):
            container_data = pd.DataFrame([container_data])
        
        # Özellikleri hazırla
        X = self.prepare_features(container_data)
        
        # Tahmin olasılıklarını al
        probabilities = self.model.predict_proba(X)[0]
        fill_probability = probabilities[1]  # Dolu olma olasılığı
        
        # Konteynerin dolu olup olmadığını belirle (eşik değeri: 0.75)
        is_full = fill_probability >= 0.75
        
        # Bu tahmin için özellik önemini al (açıklanabilirlik için)
        feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        
        return {
            'fill_probability': float(fill_probability),
            'is_full': bool(is_full),
            'confidence': float(max(probabilities)),
            'model_version': self.model_version,
            'feature_importance': feature_importance
        }
    
    def validate_citizen_report(self, container_id, user_report, container_data):
        """
        Vatandaş bildirimini model tahminine karşı doğrula
        
        Parametreler:
            container_id: Benzersiz konteyner tanımlayıcısı
            user_report: Kullanıcının bildirdiği durum ('EMPTY', 'HALF_FULL', 'FULL', 'OVERFLOWING')
            container_data: Tahmin için konteyner bilgileri
            
        Döndürür:
            Doğrulama sonucunu içeren sözlük
        """
        # Model tahminini al
        prediction = self.predict(container_data)
        fill_probability = prediction['fill_probability']
        
        # Makullük eşik değerlerini tanımla
        thresholds = {
            'EMPTY': {'min': 0.0, 'max': 0.25},
            'HALF_FULL': {'min': 0.25, 'max': 0.75},
            'FULL': {'min': 0.75, 'max': 0.90},
            'OVERFLOWING': {'min': 0.90, 'max': 1.0}
        }
        
        expected_range = thresholds.get(user_report.upper())
        
        if expected_range is None:
            return {
                'validation_result': 'REJECTED',
                'reason': 'Geçersiz bildirim durumu',
                'confidence_score': 0.0
            }
        
        # Tahminin beklenen aralıkta olup olmadığını kontrol et
        if expected_range['min'] <= fill_probability <= expected_range['max']:
            # Bildirim makul
            validation_result = 'ACCEPTED'
            confidence = prediction['confidence']
            reason = f"Bildirim model tahminiyle eşleşiyor (doluluk seviyesi: {fill_probability:.2%})"
            deviation = 0
            
        else:
            # Sapma hesapla
            if fill_probability < expected_range['min']:
                deviation = expected_range['min'] - fill_probability
            else:
                deviation = fill_probability - expected_range['max']
            
            # Sapma şiddetine göre karar ver
            if deviation < 0.20:  # %20 tolerans içinde
                validation_result = 'NEEDS_REVIEW'
                confidence = 0.5
                reason = f"Modelden küçük sapma ({deviation:.2%}). İnceleme için işaretlendi."
            elif deviation < 0.40:  # %20-40 sapma
                validation_result = 'REJECTED'
                confidence = 0.7
                reason = f"Modelden orta seviye sapma ({deviation:.2%}). Bildirim reddedildi."
            else:  # > %40 sapma
                validation_result = 'REJECTED'
                confidence = 0.95
                reason = f"Modelden önemli sapma ({deviation:.2%}). Bildirim oldukça makul dışı."
        
        return {
            'validation_result': validation_result,
            'confidence_score': confidence,
            'reason': reason,
            'model_prediction': fill_probability,
            'user_claim': user_report,
            'deviation': deviation,
            'container_id': container_id
        }
    
    def save_model(self, filepath):
        """Eğitilmiş modeli diske kaydet"""
        if self.model is None:
            raise ValueError("Kaydedilecek model yok. Önce modeli eğitin.")
        
        model_data = {
            'model': self.model,
            'version': self.model_version,
            'feature_columns': self.feature_columns
        }
        joblib.dump(model_data, filepath)
        print(f"Model kaydedildi: {filepath}")
    
    def load_model(self, filepath):
        """Eğitilmiş modeli diskten yükle"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.model_version = model_data['version']
        self.feature_columns = model_data['feature_columns']
        print(f"Model yüklendi: {filepath} (sürüm: {self.model_version})")


# ============== MODEL #2: DİNAMİK ROTALAMA ==============

class DynamicRouter:
    """
    Atık toplama için araç rotalarını optimize eder
    """
    
    def __init__(self, road_network_json):
        """
        Parametreler:
            road_network_json: Yol ağı JSON dosyasının yolu
        """
        self.road_network = self._load_road_network(road_network_json)
        self.vehicle_types = self._load_vehicle_types()
    
    def _load_road_network(self, json_path):
        """JSON'dan yol ağını yükle"""
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_vehicle_types(self):
        """Araç tiplerini ve özelliklerini tanımla"""
        return {
            'small_truck': {
                'capacity_liters': 5000,
                'fuel_consumption_per_km': 0.25,
                'co2_emission_per_km': 0.65,
                'compatible_types': ['plastic', 'glass', 'paper']
            },
            'large_truck': {
                'capacity_liters': 12000,
                'fuel_consumption_per_km': 0.40,
                'co2_emission_per_km': 1.05,
                'compatible_types': ['plastic', 'organic', 'glass', 'paper']
            },
            'compactor': {
                'capacity_liters': 18000,
                'fuel_consumption_per_km': 0.50,
                'co2_emission_per_km': 1.30,
                'compatible_types': ['organic']
            }
        }
    
    def select_vehicle(self, container, available_vehicles):
        """
        Konteyner toplamak için en uygun aracı seç
        
        Parametreler:
            container: Konteyner bilgilerini içeren sözlük
            available_vehicles: Mevcut araçların listesi
            
        Döndürür:
            Seçilen araç veya uygun araç yoksa None
        """
        best_vehicle = None
        best_score = float('inf')
        
        for vehicle in available_vehicles:
            # Uyumluluğu kontrol et
            vehicle_type = self.vehicle_types[vehicle['type']]
            if container['container_type'] not in vehicle_type['compatible_types']:
                continue
            
            # Kapasiteyi kontrol et
            if vehicle['current_load'] + container['estimated_tonnage'] > vehicle_type['capacity_liters']:
                continue
            
            # Skoru hesapla (mesafe + kapasite kullanımı)
            distance = self._calculate_distance(vehicle['current_location'], container['location'])
            capacity_utilization = vehicle['current_load'] / vehicle_type['capacity_liters']
            
            # Düşük skor daha iyi
            score = distance * (1 + capacity_utilization)
            
            if score < best_score:
                best_score = score
                best_vehicle = vehicle
        
        return best_vehicle
    
    def _calculate_distance(self, loc1, loc2):
        """
        İki konum arasındaki mesafeyi hesapla (basitleştirilmiş Haversine)
        
        Parametreler:
            loc1, loc2: 'lat' ve 'lng' anahtarlarını içeren sözlükler
            
        Döndürür:
            Kilometre cinsinden mesafe
        """
        # Basitleştirilmiş hesaplama (production'da düzgün yönlendirme kullanın)
        lat_diff = abs(loc1['lat'] - loc2['lat'])
        lng_diff = abs(loc1['lng'] - loc2['lng'])
        
        # Yaklaşık mesafe (derece başına 111 km)
        distance = np.sqrt(lat_diff**2 + lng_diff**2) * 111
        
        return distance
    
    def optimize_route(self, containers, vehicle):
        """
        Birden fazla konteyner toplamak için optimize edilmiş rota oluştur
        
        Parametreler:
            containers: Toplanacak konteynerlerin listesi
            vehicle: Araç bilgileri
            
        Döndürür:
            Durakları içeren optimize edilmiş rota
        """
        # Açgözlü en yakın komşu algoritması
        current_location = vehicle['depot_location']
        route_stops = []
        remaining_containers = containers.copy()
        total_distance = 0
        
        while remaining_containers:
            # En yakın konteyneri bul
            nearest = None
            nearest_distance = float('inf')
            
            for container in remaining_containers:
                distance = self._calculate_distance(current_location, container['location'])
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest = container
            
            # Rotaya ekle
            route_stops.append({
                'container_id': nearest['container_id'],
                'location': nearest['location'],
                'estimated_tonnage': nearest['estimated_tonnage'],
                'distance_from_previous': nearest_distance
            })
            
            total_distance += nearest_distance
            current_location = nearest['location']
            remaining_containers.remove(nearest)
        
        # Depoya dön
        return_distance = self._calculate_distance(current_location, vehicle['depot_location'])
        total_distance += return_distance
        
        # Metrikleri hesapla
        vehicle_type = self.vehicle_types[vehicle['type']]
        fuel_consumed = total_distance * vehicle_type['fuel_consumption_per_km']
        co2_emissions = total_distance * vehicle_type['co2_emission_per_km']
        
        return {
            'vehicle_id': vehicle['vehicle_id'],
            'stops': route_stops,
            'total_distance_km': total_distance,
            'fuel_consumed_liters': fuel_consumed,
            'co2_emissions_kg': co2_emissions,
            'estimated_duration_minutes': int(total_distance / 30 * 60 + len(route_stops) * 5)
        }


# ============== ÖRNEK KULLANIM ==============

if __name__ == "__main__":
    print("=" * 60)
    print("Akıllı Atık Yönetim Sistemi - Yapay Zeka Modelleri")
    print("Nilüfer Belediyesi")
    print("=" * 60)
    
    # Örnek: Doluluk Seviyesi Tahmini
    print("\n[1] Doluluk Seviyesi Tahmin Modeli")
    print("-" * 60)
    
    predictor = FillLevelPredictor()
    
    # Simüle edilmiş eğitim verisi
    print("Not: Bu örnek koddur. Production'da gerçek veriyi CSV dosyalarından yükleyin.")
    
    # Örnek tahmin
    container_data = {
        'last_collection_date': datetime.now() - timedelta(hours=36),
        'capacity_liters': 1100,
        'population_density': 4500,
        'container_type': 'plastic',
        'avg_tonnage_last_30_days': 85.3,
        'historical_fill_rate': 0.65
    }
    
    print("\nÖrnek Konteyner Verisi:")
    for key, value in container_data.items():
        print(f"  {key}: {value}")
    
    # Not: Production'da önce eğitim gerekir
    # prediction = predictor.predict(container_data)
    # print("\nTahmin:", prediction)
    
    print("\n[2] Dinamik Rotalama Modeli")
    print("-" * 60)
    print("Not: Yol ağı JSON dosyası gereklidir (Yol-2025-12-16_13-38-47.json)")
    
    print("\n" + "=" * 60)
    print("Kurulum Tamamlandı!")
    print("=" * 60)
