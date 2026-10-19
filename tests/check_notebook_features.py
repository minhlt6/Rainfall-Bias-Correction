import json
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NB_PATH = PROJECT_ROOT / 'notebooks' / 'du_bao_mua_1h_phi_hoi_quy_banho.ipynb'

nb = json.load(open(NB_PATH, encoding='utf-8'))
ns = {'np': np, 'pd': pd}
exec(''.join(nb['cells'][3]['source']), ns)
df, create = ns['df'], ns['create_features']
features = ns['feature_cols']
assert len(features) == 23 and 'obs' not in features
original = create(df)
i = ns['split_idx']
assert original.iloc[i]['obs_lag1'] == df.iloc[i-1]['obs']
assert np.isclose(original.iloc[i]['obs_sum6h'], df.iloc[i-6:i]['obs'].sum())
assert ns['test_df'].iloc[0]['thoigian'] == df.iloc[i]['thoigian']
assert np.array_equal(ns['y_test'], ns['test_df']['obs'].values)
# Thay toàn bộ dữ liệu từ giờ t trở đi: đặc trưng quan trắc tại t không đổi.
changed = df.copy()
changed.loc[i:, 'obs'] = 12345.0
pd.testing.assert_series_equal(original.loc[i, features], create(changed).loc[i, features])
# Dự báo từ giờ t+1 trở đi không được ảnh hưởng đặc trưng tại t.
changed = df.copy()
changed.loc[i+1:, ['ecmwf_1h','gfs_1h','mblue_1h']] = 12345.0
pd.testing.assert_series_equal(original.loc[i, features], create(changed).loc[i, features])
# Cùng lịch sử, chạy đến t và chạy cả chuỗi phải tạo cùng đầu vào tại t.
pd.testing.assert_series_equal(original.loc[i, features], create(df.iloc[:i+1]).loc[i, features])
for j, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        compile(''.join(cell['source']), f'cell_{j}', 'exec')
print('PASS: 23 features; unchanged target; lag and split boundary; no current/future observation leakage; no future forecast rows; all cells compile.')
