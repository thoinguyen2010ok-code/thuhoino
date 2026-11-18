import streamlit as st
import pandas as pd
from datetime import date
import os

# --- TÍNH NĂNG MỚI: QUẢN LÝ FILE LƯU TRỮ VĨNH VIỄN ---
DATA_FILE = "dulieu_thono.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=['Tên khách nợ', 'Số tiền (VND)', 'Đã thu (VND)', 'Ngày hẹn trả', 'Trạng thái', 'Ghi chú'])
        df.to_csv(DATA_FILE, index=False)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def format_vnd(amount):
    return f"{amount:,.0f}".replace(',', '.') + " đ"

# 1. Cấu hình giao diện
st.set_page_config(page_title="Sổ Thu Nợ", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 50px; font-size: 16px; font-weight: bold; background-color: #0068c9; color: white; }
    div[data-testid="stMetricValue"] { font-size: 26px; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Sổ Quản Lý Thu Nợ")

# Luôn đọc dữ liệu mới nhất từ file (Giúp đồng bộ khi có thiết bị khác sửa)
if 'debts' not in st.session_state:
    st.session_state.debts = load_data()

# ==========================================
# PHẦN HIỂN THỊ TỔNG QUAN
# ==========================================
df = load_data() # Đọc trực tiếp từ file
tong_no = df['Số tiền (VND)'].sum() if not df.empty else 0
da_thu = df['Đã thu (VND)'].sum() if not df.empty else 0
con_lai = tong_no - da_thu

col1, col2 = st.columns(2)
col1.metric("🔴 Tổng nợ cần thu", format_vnd(tong_no))
col2.metric("🟢 Số tiền đã thu", format_vnd(da_thu))
st.metric("🟡 Số tiền còn lại (Treo nợ)", format_vnd(con_lai))

st.divider()

# ==========================================
# PHẦN QUẢN LÝ (CHIA LÀM 3 THẺ)
# ==========================================
tab1, tab2, tab3 = st.tabs(["💰 Nhập tiền thu", "➕ Thêm nợ mới", "📋 Bảng quản lý"])

with tab1:
    st.subheader("Cập nhật xác nhận tiền thu")
    current_df = load_data()
    if not current_df.empty:
        with st.form("thu_tien_form", clear_on_submit=True):
            danh_sach_khach = current_df['Tên khách nợ'].tolist()
            khach_hang = st.selectbox("Chọn người trả tiền *", danh_sach_khach)
            so_tien_tra = st.number_input("Số tiền khách trả đợt này (VND) *", min_value=0.0, step=50000.0)
            
            st.markdown(f"💵 *Số tiền bạn đang nhập:* **:blue[{format_vnd(so_tien_tra)}]**")
            
            submit_thu = st.form_submit_button("✅ XÁC NHẬN THU TIỀN")
            
            if submit_thu:
                if so_tien_tra > 0:
                    # Đọc lại file để có bản mới nhất tránh xung đột thiết bị
                    fresh_df = load_data()
                    idx = fresh_df[fresh_df['Tên khách nợ'] == khach_hang].index[0]
                    fresh_df.at[idx, 'Đã thu (VND)'] += so_tien_tra
                    
                    if fresh_df.at[idx, 'Đã thu (VND)'] >= fresh_df.at[idx, 'Số tiền (VND)']:
                        fresh_df.at[idx, 'Trạng thái'] = "✅ Đã thu xong"
                    
                    save_data(fresh_df) # LƯU VÀO FILE VĨNH VIỄN
                    st.session_state.debts = fresh_df
                    st.success(f"✅ Đã ghi nhận: {khach_hang} vừa thanh toán {format_vnd(so_tien_tra)}!")
                    st.rerun()
                else:
                    st.error("⚠️ Vui lòng nhập số tiền lớn hơn 0!")
    else:
        st.info("Chưa có danh sách nợ. Hãy qua thẻ 'Thêm nợ mới' để tạo.")

with tab2:
    with st.form("add_debt_form", clear_on_submit=True):
        name = st.text_input("Tên người nợ / Khách hàng *")
        amount = st.number_input("Số tiền nợ (VND) *", min_value=0.0, step=100000.0)
        st.markdown(f"💵 *Số tiền bạn đang nhập:* **:blue[{format_vnd(amount)}]**")
        
        date_due = st.date_input("Ngày hẹn trả", date.today())
        note = st.text_input("Ghi chú (SĐT, lý do...)")
        
        submit_add = st.form_submit_button("➕ LƯU KHOẢN NỢ")
        
        if submit_add:
            if name.strip() == "" or amount <= 0:
                st.error("⚠️ Vui lòng nhập tên người nợ và số tiền lớn hơn 0!")
            else:
                fresh_df = load_data()
                new_row = pd.DataFrame([{
                    'Tên khách nợ': name, 'Số tiền (VND)': amount, 'Đã thu (VND)': 0.0,
                    'Ngày hẹn trả': str(date_due), 'Trạng thái': '⏳ Đang chờ', 'Ghi chú': note
                }])
                fresh_df = pd.concat([fresh_df, new_row], ignore_index=True)
                
                save_data(fresh_df) # LƯU VÀO FILE VĨNH VIỄN
                st.session_state.debts = fresh_df
                st.success(f"✅ Đã thêm khoản nợ của {name} với số tiền {format_vnd(amount)}!")
                st.rerun()

with tab3:
    st.caption("Bảng theo dõi chi tiết. Sửa trạng thái bằng cách chạm vào ô tương ứng.")
    current_df = load_data()
    if not current_df.empty:
        # Chuyển đổi cột ngày tháng để hiển thị đúng định dạng trên bảng
        current_df['Ngày hẹn trả'] = pd.to_datetime(current_df['Ngày hẹn trả'], format='mixed', errors='coerce').dt.date
        
        edited_df = st.data_editor(
            current_df,
            column_config={
                "Tên khách nợ": st.column_config.TextColumn("Người nợ", disabled=True),
                "Số tiền (VND)": st.column_config.NumberColumn("Cần thu", disabled=True), 
                "Đã thu (VND)": st.column_config.NumberColumn("Đã thu", disabled=True), 
                "Ngày hẹn trả": st.column_config.DateColumn("Hẹn trả", format="DD/MM/YYYY"),
                "Trạng thái": st.column_config.SelectboxColumn(
                    "Trạng thái", options=["⏳ Đang chờ", "✅ Đã thu xong", "⚠️ Trễ hẹn", "❌ Khó đòi"], required=True
                )
            },
            hide_index=True, use_container_width=True, num_rows="dynamic"
        )
        if st.button("💾 LƯU SỬA ĐỔI BẢNG"):
            save_data(edited_df) # LƯU VÀO FILE VĨNH VIỄN
            st.session_state.debts = edited_df
            st.success("✅ Đã lưu thay đổi!")
            st.rerun()