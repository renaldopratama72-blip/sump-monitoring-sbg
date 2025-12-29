import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling: Menambahkan style khusus untuk Warning Water Balance
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .analysis-box {
        background-color: #e8f6f3; padding: 15px; border-radius: 10px; border-left: 5px solid #1abc9c;
    }
    .rec-box {
        background-color: #fef9e7; padding: 15px; border-radius: 10px; border-left: 5px solid #f1c40f;
    }
    .danger-box {
        background-color: #fdedec; padding: 15px; border-radius: 10px; border-left: 5px solid #e74c3c;
    }
    .wb-alert {
        background-color: #ffcccc; color: #cc0000; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; border: 1px solid #ff0000;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FILE MANAGEMENT SYSTEM ---
FILE_SUMP = "db_sump.csv"
FILE_POMPA = "db_pompa.csv"

def load_or_init_data():
    # 1. LOAD DATA SUMP
    if os.path.exists(FILE_SUMP):
        df_s = pd.read_csv(FILE_SUMP)
        df_s['Tanggal'] = pd.to_datetime(df_s['Tanggal'])
    else:
        # Generate Dummy Data
        data = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        for i in range(60): 
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
                    data.append({
                        "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                        "Elevasi Air (m)": round(elev, 2), "Critical Elevation (m)": 13.0,
                        "Volume Air Survey (m3)": int(elev * 5000),
                        "Plan Curah Hujan (mm)": np.random.choice([10, 20, 30]), 
                        "Curah Hujan (mm)": np.random.choice([0, 5, 15, 60]),         
                        "Actual Catchment (Ha)": 25.0, 
                        "Status": "BAHAYA" if elev > 13.0 else "AMAN"
                    })
        df_s = pd.DataFrame(data).sort_values(by=["Site", "Pit", "Tanggal"])
        df_s.to_csv(FILE_SUMP, index=False)

    # 2. LOAD DATA POMPA
    if os.path.exists(FILE_POMPA):
        df_p = pd.read_csv(FILE_POMPA)
        df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'])
    else:
        # Generate Dummy Data
        data_p = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        units = ["WP-01", "WP-02", "WP-03"] 
        for i in range(60):
            d = today - timedelta(days=i)
            for site in init_map.keys():
                for pit in init_map[site]:
                    for u in units:
                        data_p.append({
                            "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                            "Unit Code": u, 
                            "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": np.random.randint(350, 520), 
                            "EWH Plan": 20.0, "EWH Actual": round(np.random.uniform(10, 22), 1)
                        })
        df_p = pd.DataFrame(data_p)
        df_p.to_csv(FILE_POMPA, index=False)

    return df_s, df_p

# --- 3. INITIALIZE SESSION STATE ---
if 'data_sump' not in st.session_state or 'data_pompa' not in st.session_state:
    df_s, df_p = load_or_init_data()
    st.session_state['data_sump'] = df_s
    st.session_state['data_pompa'] = df_p

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

if 'site_map' not in st.session_state:
    existing_sites = st.session_state.data_sump['Site'].unique()
    current_map = {}
    for s in existing_sites:
        pits = st.session_state.data_sump[st.session_state.data_sump['Site'] == s]['Pit'].unique().tolist()
        current_map[s] = pits
    st.session_state['site_map'] = current_map

USERS = {"englcm": "eng123", "engwsl": "eng123", "engne": "eng123", "admin": "eng123"}

# --- 4. SIDEBAR ---
with st.sidebar:
    logo_filename = "1.bara tama wijaya.jpg"
    if os.path.exists(logo_filename):
        st.image(logo_filename, use_container_width=True)
    else:
        st.markdown("## 🏢 BARA TAMA WIJAYA")
    
    st.markdown("<h3 style='text-align: center;'>Water Management</h3>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state['logged_in']:
        st.success(f"👤 Login: {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
    else:
        st.info("👀 Mode: View Only")

    st.divider()
    current_sites = list(st.session_state['site_map'].keys())
    selected_site = st.selectbox("📍 Pilih Site", current_sites) if current_sites else None
    
    pit_options = ["All Sumps"]
    avail_units_list = []
    
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)

    # UNIT SELECTION
    unit_options = ["All Units"]
    if selected_pit != "All Sumps":
        raw_p = st.session_state.data_pompa
        avail_units_list = raw_p[(raw_p['Site'] == selected_site) & (raw_p['Pit'] == selected_pit)]['Unit Code'].unique().tolist()
        avail_units_list.sort()
        unit_options += avail_units_list
    
    selected_unit = st.selectbox("🚜 Pilih Unit Pompa", unit_options)
    
    st.caption("FILTER WAKTU")
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 5. MAIN LOGIC (WATER BALANCE CALC) ---
def save_to_csv():
    st.session_state.data_sump.to_csv(FILE_SUMP, index=False)
    st.session_state.data_pompa.to_csv(FILE_POMPA, index=False)

df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

# Filter Base Data
if selected_site:
    df_s = df_s[df_s['Site'] == selected_site]
    df_p = df_p[df_p['Site'] == selected_site]

if selected_pit != "All Sumps":
    df_s = df_s[df_s['Pit'] == selected_pit]
    df_p = df_p[df_p['Pit'] == selected_pit]

df_s_filt = df_s[(df_s['Tanggal'].dt.year == sel_year) & (df_s['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
df_p_filt = df_p[(df_p['Tanggal'].dt.year == sel_year) & (df_p['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")

# 1. Prepare Data for Pump Graph (Specific Unit)
if selected_unit != "All Units":
    df_p_display = df_p_filt[df_p_filt['Unit Code'] == selected_unit].sort_values(by="Tanggal")
    title_suffix = f"Unit: {selected_unit}"
else:
    df_p_display = df_p_filt.groupby('Tanggal')[['Debit Plan (m3/h)', 'Debit Actual (m3/h)', 'EWH Plan', 'EWH Actual']].mean().reset_index()
    title_suffix = "Rata-rata Semua Unit"

# 2. WATER BALANCE CALCULATION (CRITICAL PART)
# Menggunakan Total Volume Keluar dari SEMUA pompa di pit tersebut
df_p_total = df_p_filt.copy()
df_p_total['Volume Out'] = df_p_total['Debit Actual (m3/h)'] * df_p_total['EWH Actual']
daily_out = df_p_total.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()

df_wb = pd.merge(df_s_filt, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)

# Rumus Volume Hujan: Curah Hujan (mm) * Catchment (Ha) * 10
df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10

df_wb = df_wb.sort_values(by="Tanggal")
df_wb['Volume Kemarin'] = df_wb['Volume Air Survey (m3)'].shift(1)

# RUMUS UTAMA: Vol Teoritis = Vol Kemarin + Vol Hujan - Vol Pompa
df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] - df_wb['Volume Out']

# Selisih = Vol Survey - Vol Teoritis
df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']

# Error % = (Selisih Absolut / Volume Survey) * 100
df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100
df_wb_dash = df_wb # Data for dashboard

# --- FUNGSI LOGIN ---
def render_login_form(unique_key):
    with st.form(key=f"login_form_{unique_key}"):
        st.subheader("🔒 Area Terbatas")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user in USERS and USERS[user] == pwd:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.rerun()
            else:
                st.error("Gagal Login")

# --- 6. DISPLAY TABS ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia untuk filter ini.")
    else:
        last = df_wb_dash.iloc[-1]
        
        # --- METRICS SECTION ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Elevasi Air", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey (Aktual)", f"{last['Volume Air Survey (m3)']:,.0f} m³")
        c3.metric("Rainfall (Bulan)", f"{df_wb_dash['Curah Hujan (mm)'].sum()} mm")
        
        # Logic Status Box
        clr = "#27ae60"
        status_txt = "AMAN"
        if last['Status'] == "BAHAYA":
            clr = "#e74c3c"; status_txt = "BAHAYA"
        
        c4.markdown(f"<div style='background-color:{clr};color:white;padding:10px;border-radius:5px;text-align:center;'>{status_txt}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- 1. WATER BALANCE SECTION (HIGHLIGHT) ---
        st.subheader("⚖️ Water Balance: Survey vs Hitungan")
        
        # Cek Error > 5%
        last_error = last['Error %']
        is_wb_critical = False
        
        if last_error > 5.0 or pd.isna(last_error):
            is_wb_critical = True
            st.markdown(f"""
            <div class="wb-alert">
                ⚠️ PERINGATAN WATER BALANCE: Error {last_error:.1f}% (Melebihi Toleransi 5%)<br>
                Selisih Volume: {last['Diff Volume']:,.0f} m³
            </div>
            """, unsafe_allow_html=True)
        
        col_wb1, col_wb2 = st.columns([2, 1])
        
        with col_wb1:
            # Grafik Masuk vs Keluar
            fig_wb = go.Figure()
            # Masuk (Positif)
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (Rain)'], 
                name='(+) Air Masuk (Hujan)', marker_color='#3498db'
            ))
            # Keluar (Positif untuk visual perbandingan)
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Out'], 
                name='(-) Air Keluar (Pompa)', marker_color='#e74c3c'
            ))
            
            fig_wb.update_layout(
                title="Perbandingan Volume: Air Hujan Masuk vs Pompa Keluar",
                barmode='group', 
                yaxis=dict(title="Volume Air (m³)"), 
                legend=dict(orientation='h', y=1.1),
                height=400, margin=dict(t=30)
            )
            st.plotly_chart(fig_wb, use_container_width=True)
            
        with col_wb2:
            st.caption("📋 **Tabel Validasi Water Balance**")
            # Menampilkan tabel ringkas untuk validasi
            df_show = df_wb_dash[['Tanggal', 'Volume Air Survey (m3)', 'Volume Teoritis', 'Diff Volume', 'Error %']].copy()
            df_show['Tanggal'] = df_show['Tanggal'].dt.strftime('%d-%m')
            
            # Highlight kolom Error jika > 5% (Visualisasi sederhana di tabel streamlit)
            st.dataframe(df_show.style.format({
                'Volume Air Survey (m3)': '{:,.0f}',
                'Volume Teoritis': '{:,.0f}', 
                'Diff Volume': '{:,.0f}',
                'Error %': '{:.1f}%'
            }), hide_index=True, use_container_width=True, height=350)
            
            st.info("ℹ️ Vol Teoritis = Vol Kemarin + Hujan - Pompa")

        # --- 2. GRAFIK ELEVASI ---
        st.markdown("---")
        st.subheader("🌊 Tren Elevasi & Volume")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol Survey', 
            marker_color='#95a5a6', opacity=0.4, yaxis='y2'
        ))
        fig_s.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', mode='lines+markers',
            line=dict(color='#e67e22', width=3)
        ))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
        fig_s.update_layout(
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Volume (m3)"),
            yaxis=dict(title="Elevasi (m)"), legend=dict(orientation='h', y=1.1), height=350, margin=dict(t=30)
        )
        st.plotly_chart(fig_s, use_container_width=True)

        # --- 3. PERFORMA POMPA ---
        st.markdown("---")
        st.subheader(f"⚙️ Performa Pompa ({title_suffix})")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.caption(f"**Debit: Plan vs Actual (m3/h)**")
            fig_d = go.Figure()
            fig_d.add_trace(go.Bar(x=df_p_display['Tanggal'], y=df_p_display['Debit Actual (m3/h)'], name='Act', marker_color='#2ecc71'))
            fig_d.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['Debit Plan (m3/h)'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_d.update_layout(legend=dict(orientation='h', y=1.1), height=250, margin=dict(t=20))
            st.plotly_chart(fig_d, use_container_width=True)
        with col_p2:
            st.caption(f"**EWH: Plan vs Actual (Jam)**")
            fig_e = go.Figure()
            fig_e.add_trace(go.Bar(x=df_p_display['Tanggal'], y=df_p_display['EWH Actual'], name='Act', marker_color='#d35400'))
            fig_e.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['EWH Plan'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_e.update_layout(legend=dict(orientation='h', y=1.1), height=250, margin=dict(t=20))
            st.plotly_chart(fig_e, use_container_width=True)

        # --- 4. ANALISA & REKOMENDASI ---
        st.markdown("---")
        st.subheader("🧠 Analisa & Rekomendasi")
        
        last_pump_data = df_p_display[df_p_display['Tanggal'] == last['Tanggal']]
        if not last_pump_data.empty:
            avg_debit_act = last_pump_data['Debit Actual (m3/h)'].mean()
            avg_debit_plan = last_pump_data['Debit Plan (m3/h)'].mean()
        else:
            avg_debit_act = 0; avg_debit_plan = 500

        col_an, col_rec = st.columns(2)
        
        # LOGIC WARNA & PESAN
        if is_wb_critical:
            style_box = "danger-box" # Merah karena WB Error Tinggi
            header_text = "🚨 PERINGATAN: DATA TIDAK BALANCE"
        elif last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
            style_box = "danger-box"; header_text = "🚨 BAHAYA: ELEVASI TINGGI"
        elif last['Elevasi Air (m)'] >= (last['Critical Elevation (m)'] - 1.0):
            style_box = "rec-box"; header_text = "⚠️ SIAGA"
        else:
            style_box = "analysis-box"; header_text = "✅ KONDISI AMAN"

        with col_an:
            st.markdown(f"""
            <div class="{style_box}">
                <h4>{header_text}</h4>
                <ul>
                    <li><b>Status Water Balance:</b> Error {last_error:.1f}%.</li>
                    <li><b>Status Elevasi:</b> {last['Elevasi Air (m)']} m (Limit: {last['Critical Elevation (m)']} m).</li>
                    <li><b>Volume Survey:</b> {last['Volume Air Survey (m3)']:,.0f} m³.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_rec:
            st.markdown('<div class="rec-box"><h4>🛠️ REKOMENDASI</h4>', unsafe_allow_html=True)
            rec_list = []
            
            # REKOMENDASI KHUSUS WATER BALANCE
            if is_wb_critical:
                rec_list.append("🔴 <b>CEK DEBIT POMPA ACTUAL:</b> Kemungkinan debit aktual lebih kecil dari laporan, atau unit breakdown tidak tercatat.")
                rec_list.append("🔴 <b>CEK CATCHMENT AREA:</b> Pastikan luasan catchment area (Ha) terupdate sesuai progress tambang.")
                rec_list.append("🔴 <b>CEK OTHER INFLOW:</b> Periksa potensi <b>Seepage atau Groundwater</b> yang masuk ke Sump namun belum terhitung.")
            
            # REKOMENDASI OPERASIONAL
            if last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
                rec_list.append("⛔ <b>STOP OPERASI & EVAKUASI UNIT.</b>")
            if avg_debit_act < (avg_debit_plan * 0.85):
                rec_list.append(f"🔧 Cek Unit <b>{selected_unit}</b>: Debit di bawah target.")
            
            if not rec_list: st.markdown("- ✅ Data Valid & Operasi Aman.")
            for r in rec_list: st.markdown(f"- {r}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        render_login_form(unique_key="input_tab")
    else:
        st.info("Data Sump (Elevasi/Hujan) & Data Pompa (Unit/Debit).")
        with st.expander("➕ Input Harian Baru", expanded=True):
            d_in = st.date_input("Tanggal", date.today())
            p_in = st.selectbox("Sump", st.session_state['site_map'].get(selected_site, []), key="pi")
            
            cl, cr = st.columns(2)
            with cl:
                with st.form("fs"):
                    st.markdown("<b>Data Sump & Hujan</b>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    e_a = c1.number_input("Elevasi (m)", format="%.2f")
                    v_a = c2.number_input("Volume Survey (m3)", step=100)
                    r_p = c1.number_input("Rain Plan (mm)", 0.0)
                    r_a = c2.number_input("Rain Act (mm)", 0.0)
                    if st.form_submit_button("Simpan Sump"):
                        new = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                            "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                            "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                            "Status": "BAHAYA" if e_a > 13 else "AMAN"
                        }
                        st.session_state.data_sump = pd.concat([pd.DataFrame([new]), st.session_state.data_sump], ignore_index=True)
                        save_to_csv(); st.success("Sump Saved!")
            with cr:
                with st.form("fp"):
                    st.markdown("<b>Data Pompa</b>", unsafe_allow_html=True)
                    uc = st.text_input("Unit Code (e.g., WP-01)")
                    da = st.number_input("Debit Actual (m3/h)", 0)
                    ea = st.number_input("EWH Actual (Jam)", 0.0)
                    if st.form_submit_button("Simpan Pompa"):
                        newp = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Unit Code": uc, "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": da,
                            "EWH Plan": 20.0, "EWH Actual": ea
                        }
                        st.session_state.data_pompa = pd.concat([pd.DataFrame([newp]), st.session_state.data_pompa], ignore_index=True)
                        save_to_csv(); st.success("Pompa Saved!")

        st.divider()
        t1, t2 = st.tabs(["Edit Sump", "Edit Pompa"])
        with t1:
            ed_s = st.data_editor(st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site], num_rows="dynamic", key="es")
            if st.button("Save Sump Changes"):
                st.session_state.data_sump = pd.concat([st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site], ed_s], ignore_index=True)
                save_to_csv(); st.rerun()
        with t2:
            ed_p = st.data_editor(st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site], num_rows="dynamic", key="ep")
            if st.button("Save Pump Changes"):
                st.session_state.data_pompa = pd.concat([st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site], ed_p], ignore_index=True)
                save_to_csv(); st.rerun()

# TAB 3 & 4 (Database & Admin)
with tab_db:
    c1, c2 = st.columns(2)
    c1.download_button("Download Sump CSV", st.session_state.data_sump.to_csv(index=False), "sump.csv")
    c2.download_button("Download Pompa CSV", st.session_state.data_pompa.to_csv(index=False), "pompa.csv")
    st.dataframe(st.session_state.data_sump)

with tab_admin:
    if st.session_state['logged_in']:
        ns = st.text_input("New Site Name")
        if st.button("Add Site") and ns: st.session_state['site_map'][ns] = []
    else: render_login_form("adm")
