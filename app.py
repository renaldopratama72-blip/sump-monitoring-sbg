import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np
import os
import sqlite3

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agar Data Dummy STABIL
np.random.seed(42)

# CSS Styling
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
    .date-header {
        font-size: 1.2rem; font-weight: bold; color: #2c3e50; margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE SYSTEM (SQLite) ---
DB_FILE = "water_management.db"

def get_db_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    """Membuat tabel dan mengisi dummy data jika database baru"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Cek apakah tabel sudah ada
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sump'")
    table_exists = c.fetchone()
    
    if not table_exists:
        # Create Tables
        c.execute('''CREATE TABLE sump (
            Tanggal TEXT, Site TEXT, Pit TEXT, Elevasi_Air REAL, Critical_Elevation REAL,
            Volume_Air_Survey REAL, Plan_Curah_Hujan REAL, Curah_Hujan REAL,
            Actual_Catchment REAL, Groundwater REAL, Status TEXT)''')
            
        c.execute('''CREATE TABLE pompa (
            Tanggal TEXT, Site TEXT, Pit TEXT, Unit_Code TEXT,
            Debit_Plan REAL, Debit_Actual REAL, EWH_Plan REAL, EWH_Actual REAL)''')
        
        # --- GENERATE DUMMY DATA (Logic asli Anda dipindahkan ke sini) ---
        data_s = []
        data_p = []
        today = date.today()
        init_map = {
            "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
            "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
            "Nusantara Energy (NE)": ["Sump S8"]
        }
        units = ["WP-01", "WP-02"]
        
        for i in range(30):
            d = today - timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            for site in init_map.keys():
                for pit in init_map[site]:
                    # Sump Data
                    elev = 10.0 + (np.sin(i/10) * 2)
                    data_s.append((
                        d_str, site, pit, round(elev, 2), 13.0, int(elev * 5000), 20.0,
                        np.random.randint(0, 40), 25.0, 0.0, "BAHAYA" if elev > 13.0 else "AMAN"
                    ))
                    # Pompa Data
                    for u in units:
                        data_p.append((
                            d_str, site, pit, u, 500, np.random.randint(400, 500), 20.0, round(np.random.uniform(15, 20), 1)
                        ))
        
        c.executemany('INSERT INTO sump VALUES (?,?,?,?,?,?,?,?,?,?,?)', data_s)
        c.executemany('INSERT INTO pompa VALUES (?,?,?,?,?,?,?,?)', data_p)
        conn.commit()
        
    conn.close()

def load_data():
    """Load data dari SQLite ke Pandas DataFrame"""
    init_db() # Pastikan DB siap
    conn = get_db_connection()
    
    # Load Sump & Rename Columns back to Display Format
    df_s = pd.read_sql("SELECT * FROM sump", conn)
    df_s['Tanggal'] = pd.to_datetime(df_s['Tanggal'])
    df_s = df_s.rename(columns={
        "Elevasi_Air": "Elevasi Air (m)", "Critical_Elevation": "Critical Elevation (m)",
        "Volume_Air_Survey": "Volume Air Survey (m3)", "Plan_Curah_Hujan": "Plan Curah Hujan (mm)",
        "Curah_Hujan": "Curah Hujan (mm)", "Actual_Catchment": "Actual Catchment (Ha)",
        "Groundwater": "Groundwater (m3)"
    })

    # Load Pompa & Rename Columns back to Display Format
    df_p = pd.read_sql("SELECT * FROM pompa", conn)
    df_p['Tanggal'] = pd.to_datetime(df_p['Tanggal'])
    df_p = df_p.rename(columns={
        "Unit_Code": "Unit Code", "Debit_Plan": "Debit Plan (m3/h)",
        "Debit_Actual": "Debit Actual (m3/h)", "EWH_Plan": "EWH Plan", "EWH_Actual": "EWH Actual"
    })
    
    conn.close()
    return df_s.sort_values(by=["Site", "Pit", "Tanggal"]), df_p

def save_new_sump_to_db(data):
    """Menyimpan 1 baris input baru ke SQLite"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO sump VALUES (?,?,?,?,?,?,?,?,?,?,?)", (
        data['Tanggal'].strftime('%Y-%m-%d'), data['Site'], data['Pit'],
        data['Elevasi Air (m)'], data['Critical Elevation (m)'], data['Volume Air Survey (m3)'],
        data['Plan Curah Hujan (mm)'], data['Curah Hujan (mm)'], data['Actual Catchment (Ha)'],
        data['Groundwater (m3)'], data['Status']
    ))
    conn.commit()
    conn.close()

def save_new_pompa_to_db(data):
    """Menyimpan 1 baris input pompa baru ke SQLite"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO pompa VALUES (?,?,?,?,?,?,?,?)", (
        data['Tanggal'].strftime('%Y-%m-%d'), data['Site'], data['Pit'],
        data['Unit Code'], data['Debit Plan (m3/h)'], data['Debit Actual (m3/h)'],
        data['EWH Plan'], data['EWH Actual']
    ))
    conn.commit()
    conn.close()

def overwrite_full_db(df_s, df_p):
    """Fungsi untuk menu EDIT: Menimpa total database dengan data baru dari Editor"""
    conn = get_db_connection()
    
    # Prepare Sump for SQL (Rename columns to match DB schema)
    s_save = df_s.copy()
    s_save['Tanggal'] = s_save['Tanggal'].dt.strftime('%Y-%m-%d')
    s_save = s_save.rename(columns={
        "Elevasi Air (m)": "Elevasi_Air", "Critical Elevation (m)": "Critical_Elevation",
        "Volume Air Survey (m3)": "Volume_Air_Survey", "Plan Curah Hujan (mm)": "Plan_Curah_Hujan",
        "Curah Hujan (mm)": "Curah_Hujan", "Actual Catchment (Ha)": "Actual_Catchment",
        "Groundwater": "Groundwater"
    })
    s_save.to_sql('sump', conn, if_exists='replace', index=False)
    
    # Prepare Pompa for SQL
    p_save = df_p.copy()
    p_save['Tanggal'] = p_save['Tanggal'].dt.strftime('%Y-%m-%d')
    p_save = p_save.rename(columns={
        "Unit Code": "Unit_Code", "Debit Plan (m3/h)": "Debit_Plan",
        "Debit Actual (m3/h)": "Debit_Actual", "EWH Plan": "EWH_Plan", "EWH Actual": "EWH_Actual"
    })
    p_save.to_sql('pompa', conn, if_exists='replace', index=False)
    conn.close()

# --- 3. INITIALIZE SESSION STATE ---
if 'data_sump' not in st.session_state or 'data_pompa' not in st.session_state:
    # Load dari SQLite saat pertama kali buka
    df_s, df_p = load_data()
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
    # --- LOGO HANDLING ---
    logo_filename = "1.bara tama wijaya.jpg"
    if os.path.exists(logo_filename):
        st.image(logo_filename, use_container_width=True)
    else:
        st.markdown("## 🏢 BARA TAMA WIJAYA")
        st.caption("⚠️ Upload file logo ke folder repository agar gambar muncul.")

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
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)

    # UNIT SELECTION
    unit_options = ["All Units"]
    if selected_pit != "All Sumps" and not st.session_state.data_pompa.empty:
        raw_p = st.session_state.data_pompa
        avail_units_list = raw_p[(raw_p['Site'] == selected_site) & (raw_p['Pit'] == selected_pit)]['Unit Code'].unique().tolist()
        avail_units_list.sort()
        unit_options += avail_units_list
    selected_unit = st.selectbox("🚜 Pilih Unit Pompa", unit_options)
    
    st.caption("FILTER WAKTU")
    
    # Ambil tahun dari DB jika ada, jika tidak pakai tahun ini
    if not st.session_state.data_sump.empty:
        avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    else:
        avail_years = [date.today().year]
        
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 5. MAIN LOGIC (WATER BALANCE CALC) ---
# Load fresh copy for calculation
df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

# Apply Filters
if selected_site and not df_s.empty:
    df_s = df_s[df_s['Site'] == selected_site]
    df_p = df_p[df_p['Site'] == selected_site] if not df_p.empty else df_p

if selected_pit != "All Sumps" and not df_s.empty:
    df_s = df_s[df_s['Pit'] == selected_pit]
    df_p = df_p[df_p['Pit'] == selected_pit] if not df_p.empty else df_p

df_wb_dash = pd.DataFrame()
df_p_display = pd.DataFrame()
title_suffix = ""

if not df_s.empty:
    df_s_filt = df_s[(df_s['Tanggal'].dt.year == sel_year) & (df_s['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
    
    if not df_p.empty:
        df_p_filt = df_p[(df_p['Tanggal'].dt.year == sel_year) & (df_p['Tanggal'].dt.month == sel_month_int)].sort_values(by="Tanggal")
    else:
        df_p_filt = pd.DataFrame()

    # 1. Prepare Data for Pump Graph
    if not df_p_filt.empty:
        if selected_unit != "All Units":
            df_p_display = df_p_filt[df_p_filt['Unit Code'] == selected_unit].sort_values(by="Tanggal")
            title_suffix = f"Unit: {selected_unit}"
        else:
            df_p_display = df_p_filt.groupby('Tanggal')[['Debit Plan (m3/h)', 'Debit Actual (m3/h)', 'EWH Plan', 'EWH Actual']].mean().reset_index()
            title_suffix = "Rata-rata Semua Unit"

    # 2. WATER BALANCE CALCULATION
    if not df_s_filt.empty:
        if not df_p_filt.empty:
            df_p_total = df_p_filt.copy()
            df_p_total['Volume Out'] = df_p_total['Debit Actual (m3/h)'] * df_p_total['EWH Actual']
            daily_out = df_p_total.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()
            df_wb = pd.merge(df_s_filt, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
            df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)
        else:
            df_wb = df_s_filt.copy()
            df_wb['Volume Out'] = 0

        # Inflow: Rain & Groundwater
        df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
        df_wb['Volume In (GW)'] = df_wb['Groundwater (m3)'].fillna(0)

        df_wb = df_wb.sort_values(by="Tanggal")
        df_wb['Volume Kemarin'] = df_wb['Volume Air Survey (m3)'].shift(1)

        # RUMUS WATER BALANCE UPDATE
        df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] + df_wb['Volume In (GW)'] - df_wb['Volume Out']
        df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
        df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100
        df_wb_dash = df_wb 

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
        st.warning("⚠️ Data belum tersedia untuk filter ini. Silakan cek Input atau pilih bulan lain.")
    else:
        last = df_wb_dash.iloc[-1]
        
        # --- HEADER TANGGAL HARI INI ---
        st.markdown(f"<div class='date-header'>📅 Dashboard Status per Tanggal: {last['Tanggal'].strftime('%d %B %Y')}</div>", unsafe_allow_html=True)

        # --- METRICS SECTION ---
        c1, c2, c3, c4, c5 = st.columns(5)
        
        c1.metric("Elevasi Air", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f} m³")
        
        # RAINFALL TODAY VS MTD
        rain_today = last['Curah Hujan (mm)']
        rain_mtd = df_wb_dash['Curah Hujan (mm)'].sum()
        c3.metric("Rain Today", f"{rain_today} mm")
        c4.metric("Rain MTD", f"{rain_mtd} mm")
        
        status_txt = "AMAN"; clr = "#27ae60"
        if last['Status'] == "BAHAYA": clr = "#e74c3c"; status_txt = "BAHAYA"
        c5.markdown(f"<div style='background-color:{clr};color:white;padding:20px;border-radius:5px;text-align:center;font-weight:bold;'>{status_txt}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- 1. WATER BALANCE & RAINFALL ANALYSIS ---
        st.subheader("⚖️ Water Balance & Rainfall Analysis")
        
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
        
        col_wb1, col_wb2 = st.columns(2)
        
        with col_wb1:
            # CHART RAINFALL PLAN VS ACTUAL
            fig_rain = go.Figure()
            fig_rain.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'], 
                name='Act Rain (mm)', marker_color='#3498db',
                text=df_wb_dash['Curah Hujan (mm)'], textposition='auto'
            ))
            fig_rain.add_trace(go.Scatter(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'], 
                name='Plan Rain (mm)', mode='lines+markers',
                line=dict(color='#e74c3c', dash='dot')
            ))
            fig_rain.update_layout(title="Rainfall: Plan vs Actual (mm)", height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1))
            st.plotly_chart(fig_rain, use_container_width=True)

        with col_wb2:
            # CHART WATER BALANCE
            fig_wb = go.Figure()
            # Stacked Inflow
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (Rain)'], 
                name='In (Rain)', marker_color='#3498db'
            ))
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (GW)'], 
                name='In (Groundwater)', marker_color='#9b59b6'
            ))
            # Outflow - LABEL "TOTAL ALL PUMPS"
            fig_wb.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Out'], 
                name='Out (Total All Pumps)', marker_color='#e74c3c',
                text=df_wb_dash['Volume Out'], texttemplate='%{text:.0f}', textposition='auto'
            ))
            fig_wb.update_layout(title="Volume Flow (m³): In vs Out", barmode='group', height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1))
            st.plotly_chart(fig_wb, use_container_width=True)
            
        # TABEL VALIDASI
        with st.expander("📋 Lihat Detail Angka Water Balance"):
            df_show = df_wb_dash[['Tanggal', 'Volume Air Survey (m3)', 'Volume Teoritis', 'Diff Volume', 'Error %']].copy()
            df_show['Tanggal'] = df_show['Tanggal'].dt.strftime('%d-%m-%Y')
            st.dataframe(df_show.style.format({'Volume Air Survey (m3)': '{:,.0f}','Volume Teoritis': '{:,.0f}', 'Diff Volume': '{:,.0f}','Error %': '{:.1f}%'}), hide_index=True, use_container_width=True)

        # --- 2. GRAFIK ELEVASI ---
        st.markdown("---")
        st.subheader("🌊 Tren Elevasi Sump")
        fig_s = go.Figure()
        fig_s.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol', 
            marker_color='#95a5a6', opacity=0.3, yaxis='y2'
        ))
        fig_s.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', 
            mode='lines+markers+text',
            line=dict(color='#e67e22', width=3),
            text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
        ))
        fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
        fig_s.update_layout(
            yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Volume (m3)"),
            yaxis=dict(title="Elevasi (m)"), legend=dict(orientation='h', y=1.1), height=400, margin=dict(t=30)
        )
        st.plotly_chart(fig_s, use_container_width=True)

        # --- 3. PERFORMA POMPA ---
        st.markdown("---")
        st.subheader(f"⚙️ Performa Pompa ({title_suffix})")
        
        if not df_p_display.empty:
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.caption(f"**Debit: Plan vs Actual (m3/h)**")
                fig_d = go.Figure()
                fig_d.add_trace(go.Bar(
                    x=df_p_display['Tanggal'], y=df_p_display['Debit Actual (m3/h)'], name='Act', marker_color='#2ecc71',
                    text=df_p_display['Debit Actual (m3/h)'], texttemplate='%{text:.0f}', textposition='auto'
                ))
                fig_d.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['Debit Plan (m3/h)'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
                fig_d.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
                st.plotly_chart(fig_d, use_container_width=True)
            with col_p2:
                st.caption(f"**EWH: Plan vs Actual (Jam)**")
                fig_e = go.Figure()
                fig_e.add_trace(go.Bar(
                    x=df_p_display['Tanggal'], y=df_p_display['EWH Actual'], name='Act', marker_color='#d35400',
                    text=df_p_display['EWH Actual'], texttemplate='%{text:.1f}', textposition='auto'
                ))
                fig_e.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['EWH Plan'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
                fig_e.update_layout(legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=20))
                st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.info("Data Pompa tidak ditemukan untuk filter ini.")

        # --- 4. ANALISA & REKOMENDASI ---
        st.markdown("---")
        st.subheader("🧠 Analisa & Rekomendasi")
        
        col_an, col_rec = st.columns(2)
        if is_wb_critical:
            style_box = "danger-box"; header_text = "🚨 PERINGATAN: DATA TIDAK BALANCE"
        elif last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
            style_box = "danger-box"; header_text = "🚨 BAHAYA: ELEVASI TINGGI"
        else:
            style_box = "analysis-box"; header_text = "✅ KONDISI AMAN"

        with col_an:
            st.markdown(f"""
            <div class="{style_box}">
                <h4>{header_text}</h4>
                <ul>
                    <li><b>Status Water Balance:</b> Error {last_error:.1f}%.</li>
                    <li><b>Curah Hujan Hari Ini:</b> {rain_today} mm.</li>
                    <li><b>Status Elevasi:</b> {last['Elevasi Air (m)']} m.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_rec:
            st.markdown('<div class="rec-box"><h4>🛠️ REKOMENDASI</h4>', unsafe_allow_html=True)
            rec_list = []
            
            # REKOMENDASI WATER BALANCE
            if is_wb_critical:
                rec_list.append("🔴 <b>CEK INPUT DATA (HUMAN ERROR):</b> Pastikan angka Elevasi, Debit, dan Hujan yang diinput sudah benar.")
                rec_list.append("🔴 <b>Cek Groundwater:</b> Apakah ada air tanah/rembesan besar yang belum diinput di kolom Groundwater?")
                rec_list.append("🔴 <b>Cek Debit Pompa:</b> Verifikasi flowmeter pompa.")
            
            if last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
                rec_list.append("⛔ <b>STOP OPERASI & EVAKUASI UNIT.</b>")
            
            if not rec_list: st.markdown("- ✅ Data Valid & Operasi Aman.")
            for r in rec_list: st.markdown(f"- {r}", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        render_login_form(unique_key="input_tab")
    else:
        st.info("Input Data Harian (Tersimpan ke SQLite Database)")
        with st.expander("➕ Input Harian Baru", expanded=True):
            d_in = st.date_input("Tanggal", date.today())
            p_in = st.selectbox("Sump", st.session_state['site_map'].get(selected_site, []), key="pi")
            
            cl, cr = st.columns(2)
            with cl:
                with st.form("fs"):
                    st.markdown("<b>Data Sump, Hujan & Groundwater</b>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    e_a = c1.number_input("Elevasi (m)", format="%.2f")
                    v_a = c2.number_input("Volume Survey (m3)", step=100)
                    r_p = c1.number_input("Rain Plan (mm)", value=20.0)
                    r_a = c2.number_input("Rain Act (mm)", 0.0)
                    gw_v = st.number_input("Groundwater/Seepage Volume (m3)", 0.0, help="Air masuk selain hujan")
                    
                    if st.form_submit_button("Simpan Sump"):
                        new = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                            "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                            "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                            "Groundwater (m3)": gw_v,
                            "Status": "BAHAYA" if e_a > 13 else "AMAN"
                        }
                        # Save to DB
                        save_new_sump_to_db(new)
                        # Reload DB to Session State to reflect changes
                        st.session_state.data_sump, _ = load_data()
                        st.success("Sump Saved to SQLite!")
                        st.rerun()

            with cr:
                with st.form("fp"):
                    st.markdown("<b>Data Pompa (Plan vs Act)</b>", unsafe_allow_html=True)
                    uc = st.text_input("Unit Code (e.g., WP-01)")
                    c_dp, c_da = st.columns(2)
                    dp = c_dp.number_input("Debit Plan (m3/h)", value=500)
                    da = c_da.number_input("Debit Actual (m3/h)", 0)
                    ea = st.number_input("EWH Actual (Jam)", 0.0)
                    if st.form_submit_button("Simpan Pompa"):
                        newp = {
                            "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                            "Unit Code": uc, "Debit Plan (m3/h)": dp, "Debit Actual (m3/h)": da,
                            "EWH Plan": 20.0, "EWH Actual": ea
                        }
                        # Save to DB
                        save_new_pompa_to_db(newp)
                        # Reload
                        _, st.session_state.data_pompa = load_data()
                        st.success("Pompa Saved to SQLite!")
                        st.rerun()

        st.divider()
        st.markdown("### 🛠️ Edit Database (Bulk Edit)")
        st.caption("Jika Anda mengedit di tabel ini dan klik simpan, Database SQLite akan ditimpa dengan data tabel di bawah.")
        t1, t2 = st.tabs(["Edit Sump", "Edit Pompa"])
        with t1:
            ed_s = st.data_editor(st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site], num_rows="dynamic", key="es")
            if st.button("💾 UPDATE SUMP DB"):
                # Combine edited rows with others
                other_rows = st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site]
                final_s = pd.concat([other_rows, ed_s], ignore_index=True)
                
                # Update State and DB
                st.session_state.data_sump = final_s
                overwrite_full_db(st.session_state.data_sump, st.session_state.data_pompa)
                st.success("Sump Database Updated!")
                st.rerun()

        with t2:
            ed_p = st.data_editor(st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site], num_rows="dynamic", key="ep")
            if st.button("💾 UPDATE POMPA DB"):
                other_rows = st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site]
                final_p = pd.concat([other_rows, ed_p], ignore_index=True)
                
                st.session_state.data_pompa = final_p
                overwrite_full_db(st.session_state.data_sump, st.session_state.data_pompa)
                st.success("Pompa Database Updated!")
                st.rerun()

# TAB 3: DATABASE
with tab_db:
    st.info("📂 Database Source: SQLite (water_management.db)")
    c1, c2 = st.columns(2)
    # Convert DF to CSV string for download purposes only
    csv_sump = st.session_state.data_sump.to_csv(index=False)
    c1.download_button("Download Sump CSV", csv_sump, "sump_backup.csv")
    
    csv_pompa = st.session_state.data_pompa.to_csv(index=False)
    c2.download_button("Download Pompa CSV", csv_pompa, "pompa_backup.csv")
    
    st.subheader("Raw Data View")
    st.dataframe(st.session_state.data_sump)

# TAB 4: ADMIN
with tab_admin:
    if st.session_state['logged_in']:
        ns = st.text_input("New Site Name")
        if st.button("Add Site") and ns: st.session_state['site_map'][ns] = []
    else: render_login_form("adm")
