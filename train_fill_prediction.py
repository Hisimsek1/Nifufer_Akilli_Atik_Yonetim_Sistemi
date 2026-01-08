"""
NİLÜFER BELEDİYESİ - KONTEYNER DOLULUK TAHMİN MODELİ
Profesyonel Machine Learning Pipeline
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
from datetime import datetime

class FillLevelPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = {}
        self.metrics = {}
        
    def prepare_features(self, df):
        """Model için özellikleri hazırla"""
        print("\n📊 Özellikler hazırlanıyor...")
        
        # NaN değerleri temizle
        df = df.dropna(subset=['expected_fill_level', 'collection_priority'])
        
        # Hedef değişken
        y = df['expected_fill_level'].values
        
        # Özellikler
        feature_columns = [
            'days_since_collection',
            'day_of_week', 
            'month',
            'is_weekend',
            'collection_days_per_week',
            'type_encoded',
            'capacity_category',
            'population_density',
            'current_fill_level'
        ]
        
        X = df[feature_columns].copy()
        
        # capacity_category'yi encode et
        category_map = {'small': 1, 'medium': 2, 'large': 3, 'xlarge': 4}
        X['capacity_category'] = X['capacity_category'].map(category_map)
        
        # Eksik değerleri doldur (sadece numerik kolonlar için)
        X = X.fillna(X.median())
        
        print(f"✓ {len(feature_columns)} özellik kullanılıyor")
        print(f"✓ {len(X)} örnek hazırlandı")
        
        return X, y, feature_columns
    
    def train_model(self, X, y, feature_columns):
        """Modeli eğit ve optimize et"""
        print("\n🎓 Model eğitimi başlıyor...")
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Veriyi ölçeklendir
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"✓ Eğitim seti: {len(X_train)} örnek")
        print(f"✓ Test seti: {len(X_test)} örnek")
        
        # RandomForest ile başla
        print("\n🌲 RandomForest modeli eğitiliyor...")
        rf_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=4,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train, y_train)
        
        # GradientBoosting ile karşılaştır
        print("🚀 GradientBoosting modeli eğitiliyor...")
        gb_model = GradientBoostingRegressor(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        gb_model.fit(X_train, y_train)
        
        # En iyi modeli seç
        rf_score = rf_model.score(X_test, y_test)
        gb_score = gb_model.score(X_test, y_test)
        
        print(f"\n📈 Model Karşılaştırması:")
        print(f"   RandomForest R² Skoru: {rf_score:.4f}")
        print(f"   GradientBoosting R² Skoru: {gb_score:.4f}")
        
        if rf_score > gb_score:
            self.model = rf_model
            best_model_name = "RandomForest"
            print(f"\n✅ RandomForest seçildi (daha yüksek R² skoru)")
        else:
            self.model = gb_model
            best_model_name = "GradientBoosting"
            print(f"\n✅ GradientBoosting seçildi (daha yüksek R² skoru)")
        
        # Test seti üzerinde değerlendirme
        y_pred = self.model.predict(X_test)
        
        # Tahminleri 0-0.95 arasına sınırla
        y_pred = np.clip(y_pred, 0, 0.95)
        
        # Metrikleri hesapla
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        self.metrics = {
            'model_name': best_model_name,
            'mae': float(mae),
            'rmse': float(rmse),
            'r2_score': float(r2),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'timestamp': datetime.now().isoformat()
        }
        
        # Özellik önemliliği
        if hasattr(self.model, 'feature_importances_'):
            importances = self.model.feature_importances_
            self.feature_importance = dict(zip(feature_columns, importances))
        
        return X_test, y_test, y_pred
    
    def evaluate_model(self, X_test, y_test, y_pred):
        """Model performansını detaylı değerlendir"""
        print("\n" + "="*80)
        print("📊 MODEL PERFORMANS RAPORU")
        print("="*80)
        
        print(f"\n🎯 Model: {self.metrics['model_name']}")
        print(f"📅 Eğitim Tarihi: {self.metrics['timestamp']}")
        print(f"\n📐 Performans Metrikleri:")
        print(f"   • R² Score (Açıklama Gücü): {self.metrics['r2_score']:.4f}")
        print(f"   • MAE (Ortalama Hata): {self.metrics['mae']:.4f} ({self.metrics['mae']*100:.2f}%)")
        print(f"   • RMSE (Kök Ortalama Kare Hata): {self.metrics['rmse']:.4f}")
        
        print(f"\n📊 Veri Seti Boyutları:")
        print(f"   • Eğitim: {self.metrics['train_size']} konteyner")
        print(f"   • Test: {self.metrics['test_size']} konteyner")
        
        print(f"\n🔍 Özellik Önemliliği (Top 5):")
        sorted_features = sorted(self.feature_importance.items(), 
                                key=lambda x: x[1], reverse=True)
        for feature, importance in sorted_features[:5]:
            print(f"   • {feature:30s}: {importance:.4f}")
        
        # Hata analizi
        errors = np.abs(y_test - y_pred)
        print(f"\n📉 Hata Analizi:")
        print(f"   • %5'in altında hata: {(errors < 0.05).sum()} konteyner ({(errors < 0.05).mean()*100:.1f}%)")
        print(f"   • %10'un altında hata: {(errors < 0.10).sum()} konteyner ({(errors < 0.10).mean()*100:.1f}%)")
        print(f"   • %15'in altında hata: {(errors < 0.15).sum()} konteyner ({(errors < 0.15).mean()*100:.1f}%)")
        
        print("\n" + "="*80)
    
    def save_model(self):
        """Modeli ve metadata'yı kaydet"""
        print("\n💾 Model kaydediliyor...")
        
        # Model dosyası
        model_path = 'models/fill_prediction_model.pkl'
        joblib.dump(self.model, model_path)
        print(f"✓ Model kaydedildi: {model_path}")
        
        # Scaler dosyası
        scaler_path = 'models/fill_scaler.pkl'
        joblib.dump(self.scaler, scaler_path)
        print(f"✓ Scaler kaydedildi: {scaler_path}")
        
        # Metadata dosyası
        metadata = {
            'metrics': self.metrics,
            'feature_importance': self.feature_importance
        }
        metadata_path = 'models/fill_model_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✓ Metadata kaydedildi: {metadata_path}")
        
        print("\n✅ Tüm dosyalar başarıyla kaydedildi!")

def main():
    print("="*80)
    print("🚀 NİLÜFER BELEDİYESİ - DOLULUK TAHMİN MODELİ EĞİTİMİ")
    print("="*80)
    
    # Veriyi yükle
    print("\n📂 İşlenmiş veri yükleniyor...")
    df = pd.read_csv('data/processed_containers.csv')
    print(f"✓ {len(df)} konteyner verisi yüklendi")
    
    # Predictor oluştur
    predictor = FillLevelPredictor()
    
    # Özellikleri hazırla
    X, y, feature_columns = predictor.prepare_features(df)
    
    # Modeli eğit
    X_test, y_test, y_pred = predictor.train_model(X, y, feature_columns)
    
    # Değerlendir
    predictor.evaluate_model(X_test, y_test, y_pred)
    
    # Kaydet
    predictor.save_model()
    
    print("\n🎉 Model eğitimi tamamlandı!")
    print("📌 Modeli kullanmak için: joblib.load('models/fill_prediction_model.pkl')")

if __name__ == "__main__":
    main()
