from pathlib import Path
import openpyxl
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'
PROCESSED_DATA_DIR = PROJECT_ROOT / 'data' / 'processed'
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

excel_path = RAW_DATA_DIR / 'DLMUA.xlsx'
print(f"Loading workbook from {excel_path}...")
wb = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)

def read_sheet(wb, name, max_rows=21376):
    ws = wb[name]
    rows = list(ws.iter_rows(min_row=1, max_row=max_rows + 1, max_col=4, values_only=True))
    header = rows[0]
    data = rows[1:]
    return pd.DataFrame(data, columns=header)

# Chỉ đọc các sheet số liệu thực chất (1h và 24h), loại bỏ các sheet phân cấp/đúng sai dư thừa
sheets = [
    'ecmwf', 'gfs', 'mblue', 'obs',
    'ecmwf24h', 'gfs24h', 'mblue24h', 'obs24h'
]

dfs = {}
for s in sheets:
    dfs[s] = read_sheet(wb, s)

tram_map = {
    'banho': 0,
    'banho1': 1,
    'thuydienSeochongho': 2
}

stations = ['banho', 'banho1', 'thuydienSeochongho']
base_time = pd.to_datetime(dfs['obs']['thoigian'])

long_frames = []
for st in stations:
    df_st = pd.DataFrame()
    df_st['thoigian'] = base_time.dt.strftime('%Y-%m-%d %H:%M:%S')
    # Chỉ giữ lại thang và gio (loại bỏ nam và ngay gây học vẹt ngày/năm lịch sử)
    df_st['thang'] = base_time.dt.month
    df_st['gio'] = base_time.dt.hour
    df_st['tram'] = st
    df_st['tram_id'] = tram_map[st]

    # Lượng mưa 1h (điền 0.0 cho các giá trị thiếu hiếm gặp)
    df_st['ecmwf_1h'] = pd.to_numeric(dfs['ecmwf'][st], errors='coerce').fillna(0.0).round(4)
    df_st['gfs_1h'] = pd.to_numeric(dfs['gfs'][st], errors='coerce').fillna(0.0).round(4)
    df_st['mblue_1h'] = pd.to_numeric(dfs['mblue'][st], errors='coerce').fillna(0.0).round(4)
    df_st['obs_1h'] = pd.to_numeric(dfs['obs'][st], errors='coerce').fillna(0.0).round(4)

    # Lượng mưa tích lũy 24h
    df_st['ecmwf_24h'] = pd.to_numeric(dfs['ecmwf24h'][st], errors='coerce').fillna(0.0).round(4)
    df_st['gfs_24h'] = pd.to_numeric(dfs['gfs24h'][st], errors='coerce').fillna(0.0).round(4)
    df_st['mblue_24h'] = pd.to_numeric(dfs['mblue24h'][st], errors='coerce').fillna(0.0).round(4)
    df_st['obs_24h'] = pd.to_numeric(dfs['obs24h'][st], errors='coerce').fillna(0.0).round(4)

    long_frames.append(df_st)

df_all = pd.concat(long_frames, ignore_index=True)
print("Total rows:", len(df_all))

# 1. Lưu file huấn luyện riêng cho trạm 'banho' với 10 cột tinh gọn
df_banho = df_all[df_all['tram'] == 'banho'].copy()
df_banho['obs'] = df_banho['obs_1h']
cols_banho = [
    'thoigian', 'thang', 'gio',
    'ecmwf_1h', 'gfs_1h', 'mblue_1h',
    'ecmwf_24h', 'gfs_24h', 'mblue_24h',
    'obs'
]
out_banho_csv = PROCESSED_DATA_DIR / 'du_lieu_banho.csv'
df_banho[cols_banho].to_csv(out_banho_csv, index=False, encoding='utf-8')
print(f"Saved {out_banho_csv} successfully! Shape: {df_banho[cols_banho].shape}")

# 2. Lưu file tổng hợp cả 3 trạm đã tinh gọn (bỏ nam, ngay, *_phancap, dubaodungsai_*)
cols_numeric_train = [
    'thoigian', 'thang', 'gio',
    'tram', 'tram_id',
    'ecmwf_1h', 'gfs_1h', 'mblue_1h', 'obs_1h',
    'ecmwf_24h', 'gfs_24h', 'mblue_24h', 'obs_24h'
]
out_csv = PROCESSED_DATA_DIR / 'du_lieu_huan_luyen.csv'
df_all[cols_numeric_train].to_csv(out_csv, index=False, encoding='utf-8')
print(f"Saved {out_csv} successfully! Shape: {df_all[cols_numeric_train].shape}")
