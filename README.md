# Rainfall Bias Correction (Hiệu chỉnh Sai số Dự báo Lượng mưa bằng Học máy)

Dự án nghiên cứu ứng dụng các mô hình học máy có cấu trúc cây (**XGBoost**, **HistGradientBoosting**, **Random Forest**) và kỹ thuật hiệu chỉnh ngưỡng xác suất (**Equitable Threat Score - ETS**, **Two-Stage Hurdle Model**, **Ordinal Threshold Cascade**) nhằm hiệu chỉnh sai số dự báo lượng mưa 1 giờ và 24 giờ từ tổ hợp các mô hình dự báo thời tiết số trị (**ECMWF**, **GFS**, **Meteoblue**) so với số liệu quan trắc thực đo tại trạm vũ lượng kế tự động (Trạm Bản Hồ).

---

## Cấu trúc Thư mục Dự án

Dự án được tổ chức theo cấu trúc chuẩn của một dự án nghiên cứu Khoa học Dữ liệu / Học máy:

```text
Rainfall-Bias-Correction/
├── data/
│   ├── raw/                        # Dữ liệu gốc chưa qua xử lý (DLMUA.xlsx) - [Git Ignored]
│   └── processed/                  # Dữ liệu sạch dùng cho huấn luyện & đánh giá (*.csv) - [Git Ignored]
├── models/                         # Các mô hình học máy đã huấn luyện (*.joblib)
│   ├── mo_hinh_hieu_chinh_mua_banho.joblib
│   ├── mo_hinh_xgboost_banho.joblib
│   ├── mo_hinh_xgboost_banho_obs_lags.joblib
│   └── mo_hinh_xgboost_banho_obs_lags_final.joblib
├── notebooks/                      # Jupyter Notebooks thực nghiệm, huấn luyện và đánh giá mô hình
│   ├── huan_luyen_hieu_chinh_mua_banho.ipynb
│   ├── du_bao_mua_1h_phi_hoi_quy_banho.before_obs_lags.ipynb
│   └── du_bao_mua_1h_phi_hoi_quy_banho.ipynb
├── src/                            # Mã nguồn tiền xử lý dữ liệu và tạo bộ dữ liệu chuẩn
│   ├── __init__.py
│   └── prepare_dataset.py
├── tests/                          # Kịch bản kiểm thử đặc trưng và chống rò rỉ dữ liệu (data leakage)
│   └── check_notebook_features.py
├── .gitignore                      # Cấu hình ẩn và loại trừ dữ liệu (data) khỏi Git/GitHub
├── requirements.txt                # Danh sách các thư viện Python cần thiết
└── README.md                       # Tài liệu tổng quan dự án nghiên cứu
```

> **Lưu ý về Bảo mật Dữ liệu:** Toàn bộ dữ liệu quan trắc và dự báo số trị trong thư mục `data/raw/` và `data/processed/` được cấu hình ẩn trong `.gitignore` và **không đẩy lên GitHub**.

---

## Phương pháp Nghiên cứu & Thiết kế Đặc trưng

### 1. Đặc thù Bài toán Lượng mưa Giờ
- **Tính rời rạc của vũ lượng kế gầu lật:** Số liệu mưa thực đo là bội số nguyên của `0.2 mm` ($0.0, 0.2, 0.4, 0.6, \dots \text{ mm}$).
- **Mất cân bằng lớp nghiêm trọng (Zero-inflation):** Khoảng `91.13%` số giờ trong chuỗi quan trắc không có mưa ($0.0 \text{ mm}$).

### 2. Hệ thống 23 Đặc trưng Đầu vào (Không rò rỉ tương lai)
- **Thời gian (2 biến):** `thang`, `gio`.
- **Dự báo gốc 1h & 24h (6 biến):** `ecmwf_1h`, `gfs_1h`, `mblue_1h`, `ecmwf_24h`, `gfs_24h`, `mblue_24h`.
- **Thống kê tổ hợp đa mô hình - Ensemble (4 biến):** `ens_1h_mean`, `ens_1h_max`, `ens_1h_std`, `n_models_rain_1h`.
- **Cửa sổ trượt nhân quả xử lý lệch pha dự báo (4 biến):** `ecmwf_1h_roll3h_mean`, `gfs_1h_roll3h_mean`, `mblue_1h_roll3h_mean`, `ens_1h_mean_roll6h_max` (`center=False`, chỉ dùng giờ hiện tại và quá khứ).
- **Động lực quan trắc quá khứ - Autoregressive Observation Lags (7 biến):** `obs_lag1`, `obs_lag2`, `obs_lag3`, `obs_lag6`, `obs_sum3h`, `obs_sum6h`, `obs_delta1h` (chỉ trích xuất từ các giờ đo đã kết thúc trước thời điểm dự báo).

### 3. Các Kiến trúc Mô hình Thực nghiệm
1. **XGBoost Multi-Class Classifier (8 lớp rời rạc bậc `0.2 mm`)**
2. **XGBoost Ordinal Threshold Cascade (Chuỗi phân loại vượt ngưỡng thứ tự)**
3. **XGBoost Two-Stage Hurdle (Phân loại thời điểm mưa kết hợp hồi quy cường độ mưa, hiệu chỉnh ngưỡng tối ưu ETS trên tập Validation theo thời gian)**
4. **XGBoost Tweedie Regressor (`objective='reg:tweedie'`)**

---

## Hướng dẫn Cài đặt & Sử dụng

### 1. Cài đặt môi trường
```bash
pip install -r requirements.txt
```

### 2. Tiền xử lý dữ liệu
Đặt tệp dữ liệu gốc `DLMUA.xlsx` vào thư mục `data/raw/`, sau đó chạy kịch bản tiền xử lý:
```bash
python src/prepare_dataset.py
```
Kịch bản sẽ xuất ra `data/processed/du_lieu_banho.csv` và `data/processed/du_lieu_huan_luyen.csv`.

### 3. Kiểm thử tính toàn vẹn đặc trưng & chống rò rỉ dữ liệu
```bash
python tests/check_notebook_features.py
```

### 4. Chạy thực nghiệm trên Jupyter Notebook
Mở và chạy các notebook trong thư mục `notebooks/`:
- `notebooks/huan_luyen_hieu_chinh_mua_banho.ipynb`: So sánh Random Forest, HGB Poisson và Two-Stage Hurdle GBDT cho hiệu chỉnh mưa 1h và phân cấp mưa 24h.
- `notebooks/du_bao_mua_1h_phi_hoi_quy_banho.before_obs_lags.ipynb`: Thực nghiệm 4 cấu hình XGBoost trên 16 đặc trưng dự báo số trị.
- `notebooks/du_bao_mua_1h_phi_hoi_quy_banho.ipynb`: Thực nghiệm 4 cấu hình XGBoost trên 23 đặc trưng (tích hợp quan trắc quá khứ) và hiệu chỉnh ngưỡng ETS trên tập Validation.
