"""
Gerçek Verilerle Model Eğitimi
Nilüfer Belediyesi Akıllı Atık Yönetim Sistemi
"""

import pandas as pd
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import json

# Veritabanı yapılandırması
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # ŞİFRENİZİ YAZIN
    'database': 'nilufer_waste_db'
}

class RealDataPredictor:
    """Gerçek verilerle çalışan tahmin modeli"""
    
    def __init__(self):
        self.model = None
        self.model_version = "v1.0.0"
        self.feature_columns = None
        self.scaler = None
        
    def connect_db(self):
        """Veritabanına bağlan"""
        return mysql.connector.connect(**DB_CONFIG)
    
    def load_training_data(self):
        """Veritabanından eğitim verisini yükle"""
        print("\n📊 Eğitim verisi yükleniyor...")
        
        conn = self.connect_db()
        
        # Konteynerleri ve ilişkili verileri çek
        query = """
        SELECT 
            c.container_id,
            c.container_type,
            c.capacity_liters,
            c.last_collection_date,
            c.current_fill_level,
            n.population,
            n.population_density,
            n.area_km2,
            COUNT(DISTINCT ce.event_id) as collection_count,
            AVG(ce.tonnage_collected) as avg_tonnage,
            AVG(ce.fill_level_before) as avg_fill_before
        FROM containers c
        LEFT JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
        LEFT JOIN collection_events ce ON c.container_id = ce.container_id
        WHERE c.status = 'active'
        GROUP BY c.container_id
        HAVING collection_count > 0
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        print(f"✓ {len(df)} konteyner verisi yüklendi")
        return df
    
    def engineer_features(self, df):
        """Özellikleri oluştur"""
        print("\n🔧 Özellikler oluşturuluyor...")
        
        features = pd.DataFrame()
        
        # Zaman tabanlı özellikler
        df['last_collection_date'] = pd.to_datetime(df['last_collection_date'])
        current_time = datetime.now()
        
        features['hours_since_collection'] = (
            (current_time - df['last_collection_date']).dt.total_seconds() / 3600
        )
        features['days_since_collection'] = features['hours_since_collection'] / 24
        
        # Tarih özellikleri
        features['day_of_week'] = current_time.weekday()
        features['is_weekend'] = (current_time.weekday() >= 5).astype(int)
        features['month'] = current_time.month
        features['season'] = self._get_season(current_time)
        
        # Konteyner özellikleri
        features['container_capacity'] = df['capacity_liters']
        
        # Konteyner tipi encoding
        container_type_map = {
            'underground': 4,
            '770lt': 3,
            '400lt': 2,
            'plastic': 1
        }
        features['container_type_encoded'] = df['container_type'].map(
            container_type_map
        ).fillna(2)
        
        # Nüfus özellikleri
        features['population'] = df['population'].fillna(df['population'].median())
        features['population_density'] = df['population_density'].fillna(
            df['population_density'].median()
        )
        features['area_km2'] = df['area_km2'].fillna(df['area_km2'].median())
        
        # Tarihsel desenler
        features['avg_tonnage'] = df['avg_tonnage'].fillna(0)
        features['avg_fill_before'] = df['avg_fill_before'].fillna(0.5)
        features['collection_count'] = df['collection_count']
        
        # Kapasite kullanım oranı
        features['capacity_usage_rate'] = (
            features['avg_tonnage'] / (features['container_capacity'] / 1000)
        ).fillna(0.5)
        
        # Hedef değişken: konteynerin dolu olup olmadığı
        # current_fill_level >= 0.75 ise dolu
        target = (df['current_fill_level'] >= 0.75).astype(int)
        
        # Sütun adlarını sakla
        self.feature_columns = features.columns.tolist()
        
        print(f"✓ {len(features.columns)} özellik oluşturuldu")
        print(f"  Özellikler: {', '.join(features.columns[:5])}...")
        
        return features, target
    
    def _get_season(self, date):
        """Mevsimi hesapla"""
        month = date.month
        if month in [12, 1, 2]:
            return 0  # Kış
        elif month in [3, 4, 5]:
            return 1  # İlkbahar
        elif month in [6, 7, 8]:
            return 2  # Yaz
        else:
            return 3  # Sonbahar
    
    def train(self):
        """Modeli eğit"""
        print("\n" + "=" * 60)
        print("MODEL EĞİTİMİ BAŞLIYOR")
        print("=" * 60)
        
        # Veriyi yükle
        df = self.load_training_data()
        
        if len(df) < 50:
            print("\n⚠️ Yeterli eğitim verisi yok! En az 50 kayıt gerekli.")
            print(f"  Mevcut kayıt sayısı: {len(df)}")
            return False
        
        # Özellikleri oluştur
        X, y = self.engineer_features(df)
        
        # Sınıf dağılımı
        print(f"\n📊 Sınıf Dağılımı:")
        print(f"  Dolu konteynerler: {y.sum()} ({y.sum()/len(y)*100:.1f}%)")
        print(f"  Dolu olmayan: {len(y)-y.sum()} ({(len(y)-y.sum())/len(y)*100:.1f}%)")
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📦 Veri Bölümü:")
        print(f"  Eğitim: {len(X_train)} örnek")
        print(f"  Test: {len(X_test)} örnek")
        
        # Modeli eğit
        print("\n🤖 Random Forest modeli eğitiliyor...")
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'  # Dengesiz sınıflar için
        )
        
        self.model.fit(X_train, y_train)
        
        # Tahmin yap
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        # Değerlendir
        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test, y_pred_test)
        
        print("\n" + "=" * 60)
        print("MODEL SONUÇLARI")
        print("=" * 60)
        print(f"\n✓ Eğitim Doğruluğu: {train_acc:.4f} ({train_acc*100:.2f}%)")
        print(f"✓ Test Doğruluğu: {test_acc:.4f} ({test_acc*100:.2f}%)")
        
        print("\n📋 Sınıflandırma Raporu (Test Seti):")
        print(classification_report(y_test, y_pred_test, 
                                   target_names=['Dolu Değil', 'Dolu']))
        
        print("\n🔢 Confusion Matrix:")
        cm = confusion_matrix(y_test, y_pred_test)
        print(f"  True Negatives: {cm[0,0]}")
        print(f"  False Positives: {cm[0,1]}")
        print(f"  False Negatives: {cm[1,0]}")
        print(f"  True Positives: {cm[1,1]}")
        
        # Özellik önemi
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n⭐ En Önemli 10 Özellik:")
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")
        
        return True
    
    def predict_single(self, container_id):
        """Tek bir konteyner için tahmin yap"""
        conn = self.connect_db()
        cursor = conn.cursor(dictionary=True)
        
        # Konteyner bilgilerini çek
        cursor.execute("""
            SELECT 
                c.container_id,
                c.container_type,
                c.capacity_liters,
                c.last_collection_date,
                c.current_fill_level,
                n.population,
                n.population_density,
                n.area_km2
            FROM containers c
            LEFT JOIN neighborhoods n ON c.neighborhood_id = n.neighborhood_id
            WHERE c.container_id = %s
        """, (container_id,))
        
        container = cursor.fetchone()
        
        if not container:
            return None
        
        # Özellikleri oluştur
        df = pd.DataFrame([container])
        X, _ = self.engineer_features(df)
        
        # Tahmin yap
        probabilities = self.model.predict_proba(X)[0]
        fill_probability = probabilities[1]
        
        conn.close()
        
        return {
            'container_id': container_id,
            'fill_probability': float(fill_probability),
            'is_full': bool(fill_probability >= 0.75),
            'confidence': float(max(probabilities)),
            'model_version': self.model_version,
            'prediction_timestamp': datetime.now().isoformat()
        }
    
    def save_predictions_to_db(self, limit=100):
        """Tüm konteynerleri tahmin et ve veritabanına kaydet"""
        print("\n💾 Tahminler veritabanına kaydediliyor...")
        
        conn = self.connect_db()
        cursor = conn.cursor()
        
        # Aktif konteynerleri al
        cursor.execute(f"SELECT container_id FROM containers WHERE status='active' LIMIT {limit}")
        container_ids = [row[0] for row in cursor.fetchall()]
        
        saved = 0
        for cid in container_ids:
            pred = self.predict_single(cid)
            
            if pred:
                try:
                    cursor.execute("""
                        INSERT INTO predictions
                        (container_id, model_version, predicted_fill_level, 
                         confidence_score, is_full)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        pred['container_id'],
                        pred['model_version'],
                        pred['fill_probability'],
                        pred['confidence'],
                        pred['is_full']
                    ))
                    saved += 1
                except:
                    pass
        
        conn.commit()
        conn.close()
        
        print(f"✓ {saved} tahmin kaydedildi")
    
    def save_model(self, filepath='models/fill_predictor.pkl'):
        """Modeli kaydet"""
        import os
        os.makedirs('models', exist_ok=True)
        
        model_data = {
            'model': self.model,
            'version': self.model_version,
            'feature_columns': self.feature_columns,
            'trained_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        print(f"\n💾 Model kaydedildi: {filepath}")
    
    def load_model(self, filepath='models/fill_predictor.pkl'):
        """Modeli yükle"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.model_version = model_data['version']
        self.feature_columns = model_data['feature_columns']
        print(f"\n✓ Model yüklendi: {filepath}")
        print(f"  Versiyon: {self.model_version}")
        print(f"  Eğitim tarihi: {model_data.get('trained_at', 'Bilinmiyor')}")

def main():
    """Ana fonksiyon"""
    print("=" * 60)
    print("NİLÜFER BELEDİYESİ - MODEL EĞİTİMİ")
    print("Akıllı Atık Yönetim Sistemi")
    print("=" * 60)
    
    try:
        # Modeli oluştur
        predictor = RealDataPredictor()
        
        # Eğit
        success = predictor.train()
        
        if success:
            # Kaydet
            predictor.save_model()
            
            # Tahminleri veritabanına kaydet
            predictor.save_predictions_to_db(limit=200)
            
            print("\n" + "=" * 60)
            print("✅ MODEL EĞİTİMİ VE KAYIT BAŞARILI!")
            print("=" * 60)
            print("\n📁 Model dosyası: models/fill_predictor.pkl")
            print("📊 Tahminler veritabanında: predictions tablosu")
            
            # Örnek tahmin
            print("\n🔮 Örnek Tahmin:")
            pred = predictor.predict_single(1)
            if pred:
                print(f"  Konteyner ID: {pred['container_id']}")
                print(f"  Doluluk Olasılığı: {pred['fill_probability']:.2%}")
                print(f"  Dolu mu: {'Evet' if pred['is_full'] else 'Hayır'}")
                print(f"  Güven: {pred['confidence']:.2%}")
        else:
            print("\n❌ Model eğitimi başarısız!")
            
    except mysql.connector.Error as e:
        print(f"\n❌ Veritabanı hatası: {e}")
        print("\n⚠️ Lütfen önce load_data.py'yi çalıştırın!")
    except Exception as e:
        print(f"\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
