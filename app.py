import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Mining Water Management",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stAlert { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# CONFIG SITE
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# --- 2. DATA GENERATOR (UPDATED: PLAN VS ACTUAL) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    # Generate 120 hari
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0] 
            # Hujan
            rain_plan = np.random.choice([0, 10, 20, 30])
            rain_act = rain_plan + np.random.randint(-5, 10)
            if rain_act < 0: rain_act = 0
            
            # Elevasi & Volume
            elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
            vol = int(elev * 5000) # Asumsi volume curve sederhana
            
            data.append({
                "Tanggal": pd.to_datetime(d), 
                "Site": site, "Pit": pit,
                "Elevasi Air (m)": round(elev, 2), 
                "Critical Elevation (m)": 13.0,
                "Volume Air Survey (m3)": vol,
                "Plan Curah Hujan (mm)": rain_plan,   # NEW
                "Curah Hujan (mm)": rain_act,         # ACTUAL
                "Actual Catchment (Ha)": 25.0, 
                "Status": "BAHAYA" if elev > 13.0 else "AMAN"
            })
    # Sortir biar perhitungan shift() nanti benar
    df_temp = pd.DataFrame(data).sort_values(by=["Site", "Pit", "Tanggal"])
    st.session_state.data_sump = df_temp

if 'data_pompa' not in st.session_state:
    data_p = []
    today = date.today()
    units = ["WP-01", "WP-02"] 
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0]
            for u in units:
                # EWH & Debit
                ewh_plan = 20.0
                ewh_act = np.random.uniform(15, 22)
                d_plan = 500
                d_act = np.random.randint(400, 480)
                
                data_p.append({
                    "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                    "Unit Code": u, 
                    "Debit Plan (m3/h)": d_plan, 
                    "Debit Actual (m3/h)": d_act, 
                    "EWH Plan": ewh_plan,           # NEW
                    "EWH Actual": round(ewh_act, 1) # ACTUAL
                })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Ensure types
st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🌊 Water Control")
    st.caption("FILTER LOKASI")
    selected_site = st.selectbox("📍 Site", ["All Sites"] + list(SITE_MAP.keys()))
    pit_options = ["All Pits"]
    if selected_site != "All Sites": pit_options += SITE_MAP[selected_site]
    selected_pit = st.selectbox("⛏️ Pit", pit_options)
    
    st.caption("FILTER WAKTU")
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("📅 Tahun", avail_years)
    
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 4. FILTERING & CALCULATION ENGINE ---
# Filter Data Dasar
df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_s = df_s[df_s['Site'] == selected_site]
    df_p = df_p[df_p['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_s = df_s[df_s['Pit'] == selected_pit]
        df_p = df_p[df_p['Pit'] == selected_pit]

# Filter Periode
df_s_filt = df_s[(df_s['Tanggal'].dt.year == sel_year) & (df_s['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
df_p_filt = df_p[(df_p['Tanggal'].dt.year == sel_year) & (df_p['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")

# --- WATER BALANCE CALCULATION LOGIC ---
# 1. Hitung Total Water Out per Hari (Gabungan semua pompa di pit tsb)
df_p_daily = df_p.copy()
df_p_daily['Volume Out'] = df_p_daily['Debit Actual (m3/h)'] * df_p_daily['EWH Actual']
daily_out = df_p_daily.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()

# 2. Gabung ke Data Sump
df_wb = pd.merge(df_s, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)

# 3. Hitung Water In (Hujan)
# Rumus: Curah Hujan (mm) * Catchment (Ha) * 10 = m3
df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10

# 4. Shift Volume untuk daptkan "Volume Kemarin"
# Pastikan urut per Site/Pit/Tanggal
df_wb = df_wb.sort_values(by=['Site', 'Pit', 'Tanggal'])
df_wb['Volume Kemarin'] = df_wb.groupby(['Site', 'Pit'])['Volume Air Survey (m3)'].shift(1)

# 5. Hitung Volume Teoritis (Calculated)
df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] - df_wb['Volume Out']

# 6. Hitung Selisih & Persentase Error
df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100

# Filter kembali untuk tampilan dashboard (Bulan terpilih)
df_wb_dash = df_wb[
    (df_wb['Tanggal'].dt.year == sel_year) & 
    (df_wb['Tanggal'].dt.month == sel_month_int)
].sort_values(by="Tanggal")


# --- 5. TABS INTERFACE ---
tab_dash, tab_input, tab_db = st.tabs(["📊 Dashboard & Water Balance", "📝 Input & Planning", "📂 Database"])

# =========================================
# TAB 1: DASHBOARD
# =========================================
with tab_dash:
    st.title(f"Laporan: {sel_month_name} {sel_year}")
    
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia. Silakan input data terlebih dahulu.")
    else:
        # A. METRIK UTAMA
        last_row = df_wb_dash.iloc[-1]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Elevasi Terkini", f"{last_row['Elevasi Air (m)']} m", f"Limit: {last_row['Critical Elevation (m)']} m", delta_color="off")
        c2.metric("Volume Survey", f"{last_row['Volume Air Survey (m3)']:,.0f} m³")
        c3.metric("Curah Hujan Bulan Ini", f"{df_wb_dash['Curah Hujan (mm)'].sum():.1f} mm")
        
        status_clr = "#e74c3c" if last_row['Status'] == "BAHAYA" else "#27ae60"
        c4.markdown(f"<div style='background-color:{status_clr};color:white;padding:10px;border-radius:5px;text-align:center;'><b>{last_row['Status']}</b></div>", unsafe_allow_html=True)

        st.markdown("---")
        
        # B. WATER BALANCE CHECKER (FITUR BARU)
        st.subheader("⚖️ Water Balance Check (Harian)")
        st.caption("Validasi: Apakah (Vol Kemarin + Hujan - Pompa) ≈ Vol Survey Hari Ini?")
        
        # Ambil data hari terakhir saja untuk highlight alert
        wb_today = last_row
        
        # Tampilan Card Water Balance Hari Terakhir
        wb_col1, wb_col2, wb_col3, wb_col4, wb_col5 = st.columns(5)
        wb_col1.metric("1. Vol Kemarin", f"{wb_today['Volume Kemarin']:,.0f}")
        wb_col2.metric("2. Air Masuk (Hujan)", f"{wb_today['Volume In (Rain)']:,.0f}", f"CH: {wb_today['Curah Hujan (mm)']} mm")
        wb_col3.metric("3. Air Keluar (Pompa)", f"{wb_today['Volume Out']:,.0f}")
        wb_col4.metric("4. Vol Hitungan", f"{wb_today['Volume Teoritis']:,.0f}", "1 + 2 - 3")
        wb_col5.metric("5. Vol Survey (Aktual)", f"{wb_today['Volume Air Survey (m3)']:,.0f}")
        
        # LOGIC ALERT MERAH
        error_val = wb_today['Error %']
        diff_val = wb_today['Diff Volume']
        
        if pd.notna(error_val) and error_val > 5.0:
            st.error(f"""
            🚨 **WATER BALANCE MISMATCH DETECTED!** (Selisih: {error_val:.1f}% / {diff_val:,.0f} m³)
            
            **Saran Perbaikan Data:**
            1. 🛑 **Cek Debit Pompa Actual:** Apakah input debit/HM terlalu besar/kecil?
            2. 🛑 **Cek Catchment Area:** Apakah luasan catchment berubah (progress tambang)?
            3. 🛑 **Cek Sumber Air Lain:** Apakah ada *Seepage*, *Groundwater*, atau *Run-off* dari area lain yang belum terhitung?
            4. 🛑 **Cek Survey:** Konfirmasi ulang data elevasi/volume survey.
            """)
        else:
            st.success(f"✅ Water Balance Valid (Selisih: {error_val:.1f}%) - Data Hidrologi Masuk Akal.")

        st.markdown("---")

        # C. GRAFIK CURAH HUJAN (PLAN VS ACTUAL)
        st.subheader("🌧️ Curah Hujan: Plan vs Actual")
        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'],
            name='Plan Rain (mm)', marker_color='lightgrey'
        ))
        fig_rain.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'],
            name='Actual Rain (mm)', marker_color='#2c3e50',
            text=df_wb_dash['Curah Hujan (mm)'], textposition='outside'
        ))
        fig_rain.update_layout(barmode='group', xaxis_title="Tanggal", yaxis_title="Curah Hujan (mm)", height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig_rain, use_container_width=True)

        # D. GRAFIK POMPA (DIPISAH: DEBIT & EWH)
        st.markdown("---")
        st.subheader("⚙️ Performa Pompa (Plan vs Actual)")
        
        if not df_p_filt.empty:
            p_units = df_p_filt['Unit Code'].unique()
            sel_unit = st.selectbox("Pilih Unit Pompa:", p_units)
            
            # Filter Data Unit
            df_u = df_p_filt[df_p_filt['Unit Code'] == sel_unit].sort_values(by="Tanggal")
            
            c_pump1, c_pump2 = st.columns(2)
            
            # GRAFIK 1: DEBIT
            with c_pump1:
                st.markdown("##### 1. Debit (Flowrate)")
                fig_d = go.Figure()
                fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Plan (m3/h)'], name='Plan Debit', marker_color='#bdc3c7'))
                fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Actual (m3/h)'], name='Actual Debit', marker_color='#27ae60',
                                      text=df_u['Debit Actual (m3/h)'], textposition='auto'))
                fig_d.update_layout(barmode='group', yaxis_title="m3/h", legend=dict(orientation="h", y=1.1), height=350, margin=dict(t=20))
                st.plotly_chart(fig_d, use_container_width=True)
                
            # GRAFIK 2: EWH (JAM JALAN)
            with c_pump2:
                st.markdown("##### 2. EWH (Jam Kerja)")
                fig_e = go.Figure()
                fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Plan'], name='Plan EWH', marker_color='#bdc3c7'))
                fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Actual'], name='Actual EWH', marker_color='#e67e22',
                                      text=df_u['EWH Actual'], textposition='auto'))
                fig_e.update_layout(barmode='group', yaxis_title="Jam", legend=dict(orientation="h", y=1.1), height=350, margin=dict(t=20))
                st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.info("Data pompa tidak ditemukan.")

# =========================================
# TAB 2: INPUT & PLANNING
# =========================================
with tab_input:
    st.subheader("📝 Input Harian (Termasuk Plan)")
    
    with st.container():
        c_in1, c_in2, c_in3 = st.columns(3)
        date_in = c_in1.date_input("Tanggal Data", date.today())
        site_in = c_in2.selectbox("Site", list(SITE_MAP.keys()), key="s_in")
        pit_in = c_in3.selectbox("Pit", SITE_MAP[site_in], key="p_in")
    
    st.markdown("---")
    col_l, col_r = st.columns(2)
    
    # FORM SUMP
    with col_l:
        st.markdown("#### 1. Hidrologi & Curah Hujan")
        with st.form("f_sump"):
            c_s1, c_s2 = st.columns(2)
            e_act = c_s1.number_input("Elevasi Aktual (m)", format="%.2f")
            e_crit = c_s2.number_input("Critical Level (m)", value=13.0)
            vol = c_s1.number_input("Volume Survey (m3)", step=100)
            catch = c_s2.number_input("Catchment Area (Ha)", format="%.2f")
            
            st.markdown("---")
            c_rain1, c_rain2 = st.columns(2)
            rain_plan = c_rain1.number_input("Plan Hujan (mm)", value=0.0)
            rain_act = c_rain2.number_input("Actual Hujan (mm)", value=0.0)
            
            if st.form_submit_button("💾 Simpan Data Sump"):
                # Simpan logic here
                new_row = {
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                    "Volume Air Survey (m3)": vol, 
                    "Plan Curah Hujan (mm)": rain_plan, "Curah Hujan (mm)": rain_act,
                    "Actual Catchment (Ha)": catch, "Status": "BAHAYA" if e_act > e_crit else "AMAN"
                }
                st.session_state.data_sump = pd.concat([pd.DataFrame([new_row]), st.session_state.data_sump], ignore_index=True)
                st.success("Data Sump Tersimpan!")

    # FORM POMPA
    with col_r:
        st.markdown("#### 2. Data Pompa (Plan vs Act)")
        with st.form("f_pump"):
            u_code = st.text_input("Kode Unit (Contoh: WP-01)")
            
            c_p1, c_p2 = st.columns(2)
            d_plan = c_p1.number_input("Plan Debit (m3/h)", value=500)
            d_act = c_p2.number_input("Actual Debit (m3/h)", value=480)
            
            c_p3, c_p4 = st.columns(2)
            ewh_plan = c_p3.number_input("Plan EWH (Jam)", value=20.0, max_value=24.0)
            ewh_act = c_p4.number_input("Actual EWH (Jam)", value=18.5, max_value=24.0)
            
            if st.form_submit_button("💾 Simpan Data Pompa"):
                new_p = {
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Unit Code": u_code, 
                    "Debit Plan (m3/h)": d_plan, "Debit Actual (m3/h)": d_act,
                    "EWH Plan": ewh_plan, "EWH Actual": ewh_act
                }
                st.session_state.data_pompa = pd.concat([pd.DataFrame([new_p]), st.session_state.data_pompa], ignore_index=True)
                st.success(f"Data Pompa {u_code} Tersimpan!")

# =========================================
# TAB 3: DATABASE
# =========================================
with tab_db:
    st.subheader("📂 Download Data Gabungan")
    dl_site = st.selectbox("Pilih Site Download:", list(SITE_MAP.keys()))
    
    # Logic Merge Data untuk Download
    df_s_dl = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
    df_p_dl = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
    
    if not df_s_dl.empty:
        df_join = pd.merge(df_s_dl, df_p_dl, on=['Tanggal', 'Site', 'Pit'], how='outer', suffixes=('_Sump', '_Pump'))
        st.dataframe(df_join.head(), use_container_width=True)
        st.download_button("⬇️ Download CSV Gabungan", df_join.to_csv(index=False).encode('utf-8'), f"Report_{dl_site}.csv", "text/csv")
    else:
        st.warning("Data kosong.")
