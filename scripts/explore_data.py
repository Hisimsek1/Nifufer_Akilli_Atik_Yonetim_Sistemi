import pandas as pd
import os

os.chdir('data')

files = ['all_merged_data.csv', 'container_counts.csv', 'tonnages.csv', 'neighbor_days_rotations.csv']

for f in files:
    try:
        df = pd.read_csv(f, encoding='utf-8', on_bad_lines='skip')
        print(f'\n📁 {f}:')
        print(f'Satır: {len(df)}, Sütun: {len(df.columns)}')
        print(f'Kolonlar: {list(df.columns)}')
        print(df.head(3))
        print('-' * 80)
    except Exception as e:
        print(f'❌ {f} hatası: {e}')
