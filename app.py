import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Mining Water Management System",
    page_icon="🌊",
    layout="wide"
)

# --- CONFIG SITE & PIT ---
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# --- 2. SETUP DATA DUMMY (DATA AWAL) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    
    # Generate data dummy 7 hari ke belakang
    for i in range(7): 
        tgl = today - timedelta(days=i)
        for site, pit_list in SITE_MAP.items():
            for pit in pit_list:
                # Simulasi Data
                elevasi = np.random.uniform(5, 40)
                crit = 45.0 if "WSL" in site else 12.0 # Contoh critical beda2
                
                data.append({
                    "Tanggal": tgl,
                    "Site": site,
                    "Pit": pit,
                    "Elevasi Air (m)": round(elevasi, 2),        # Poin 1
                    "Critical Elevation (m)": crit,              # Poin 2
                    "Volume Air Survey (m3)": int(elevasi * 2000), # Poin 3
                    "Curah Hujan (mm)": np.random.choice([0, 0, 45, 12]), # Poin 4
                    "Actual Catchment (Ha)": 25.5,               # Poin 5
                    "Status": "BAHAYA" if elevasi > crit else "AMAN" # Auto Calc
                })
    
    df_initial = pd.DataFrame(data)
    df_initial = df_initial.sort_values(by=['Site', 'Pit', 'Tanggal'], ascending=[True, True, False])
    st.session_state.data_sump = df_initial

if 'data_pompa' not in st.session_state:
    pump_data = []
    # Dummy data untuk pompa
    dates = st.session_state.data_sump['Tanggal'].unique()
    for d in dates:
        # Contoh data
        pump_data.append({
            "Tanggal": d, "Site": "Lais Coal Mine (LCM)", "Pit": "Pit Wijaya Barat", 
            "Unit Code": "WP1203", 
            "Debit Plan (m3/h)": 500,     # Poin 6a
            "Debit Actual (m3/h)": 480,   # Poin 6b
            "HM Running": 12.5            # Tambahan wajib untuk hitung total volume keluar
        })
        pump_data.append({
            "Tanggal": d, "Site": "Wiraduta Sejahtera Langgeng (WSL)", "Pit": "Pit F01", 
            "Unit Code": "WP2001", 
            "Debit Plan (m3/h)": 400, 
            "Debit Actual (m3/h)": 350,
            "HM Running": 20.0
        })
    
    st.session_state.data_pompa = pd.DataFrame(pump_data)

# --- 3. SIDEBAR & FILTER ---
st.sidebar.title("🌊 Sump Monitor")
menu = st.sidebar.radio("Menu Utama:", ["Dashboard Analisis", "Input & Edit Data"])

st.sidebar.divider()
st.sidebar.subheader("Filter Lokasi")
selected_site = st.sidebar.selectbox("Pilih Site:", ["All Sites"] + list(SITE_MAP.keys()))

selected_pit = "All Pits"
if selected_site != "All Sites":
    available_pits = ["All Pits"] + SITE_MAP[selected_site]
    selected_pit = st.sidebar.selectbox("Pilih Pit:", available_pits)

# Filter Logic
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# --- 4. HALAMAN INPUT & EDIT (SESUAI REQUEST) ---
if menu == "Input & Edit Data":
    st.title("📝 Input Data Harian")
    st.markdown("Silakan isi 6 poin data utama di bawah ini.")
    
    # --- TAB 1: DATA SUMP (5 POIN PERTAMA) ---
    st.subheader("1. Data Sump & Hidrologi")
    st.info("Poin Input: Elevasi, Critical, Volume Survey, Hujan, Catchment.")
    
    sump_config = {
        "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys()), required=True),
        "Pit": st.column_config.SelectboxColumn(options=["Pit Wijaya Barat", "Pit Wijaya Timur", "Pit F01", "Pit F02", "Pit S8"], required=True),
        "Tanggal": st.column_config.DateColumn(format="DD/MM/YYYY"),
        
        # --- 5 POIN INPUT UTAMA ---
        "Elevasi Air (m)": st.column_config.NumberColumn(help="Point 1: Elevasi Aktual", format="%.2f m", required=True),
        "Critical Elevation (m)": st.column_config.NumberColumn(help="Point 2: Batas Kritis", format="%.2f m", required=True),
        "Volume Air Survey (m3)": st.column_config.NumberColumn(help="Point 3: Volume by Survey", format="%d m³", required=True),
        "Curah Hujan (mm)": st.column_config.NumberColumn(help="Point 4: Rain Gauge", format="%.1f mm"),
        "Actual Catchment (Ha)": st.column_config.NumberColumn(help="Point 5: Luasan Catchment Aktual", format="%.2f Ha"),
        # --------------------------
        
        "Status": st.column_config.TextColumn(disabled=True) # Auto-calculated
    }
    
    edited_sump = st.data_editor(
        df_sump, 
        num_rows="dynamic", use_container_width=True,
        column_config=sump_config,
        key="editor_sump"
    )
    
    if st.button("Simpan Data Sump"):
        st.session_state.data_sump = edited_sump
        # Update Logic Status
        st.session_state.data_sump['Status'] = np.where(
            st.session_state.data_sump['Elevasi Air (m)'] > st.session_state.data_sump['Critical Elevation (m)'], 
            'BAHAYA', 'AMAN'
        )
        st.success("✅ Data Sump Tersimpan!")
        st.rerun()

    st.divider()

    # --- TAB 2: DATA POMPA (POIN KE-6) ---
    st.subheader("2. Data Debit Pompa")
    st.info("Poin Input: Debit Plan vs Debit Actual.")
    
    pump_config = {
            "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys())),
            "Pit": st.column_config.SelectboxColumn(options=["Pit Wijaya Barat", "Pit Wijaya Timur", "Pit F01", "Pit F02", "Pit S8"]),
            "Unit Code": st.column_config.TextColumn(required=True),
            
            # --- POIN 6 INPUT UTAMA ---
            "Debit Plan (m3/h)": st.column_config.NumberColumn(help="Point 6a: Kapasitas Plan", format="%d", required=True),
            "Debit Actual (m3/h)": st.column_config.NumberColumn(help="Point 6b: Flowrate Aktual di lapangan", format="%d", required=True),
            # --------------------------
            
            "HM Running": st.column_config.NumberColumn(label="Jam Jalan (HM)", help="Diperlukan untuk hitung total volume keluar", format="%.1f")
    }
    
    edited_pompa = st.data_editor(
        df_pompa,
        num_rows="dynamic", use_container_width=True,
        column_config=pump_config,
        key="editor_pompa"
    )
    
    if st.button("Simpan Data Pompa"):
        st.session_state.data_pompa = edited_pompa
        st.success("✅ Data Pompa Tersimpan!")
        st.rerun()

# --- 5. HALAMAN DASHBOARD (VISUALISASI HASIL INPUT) ---
elif menu == "Dashboard Analisis":
    st.title(f"Dashboard: {selected_site}")
    if selected_pit != "All Pits":
        st.caption(f"Lokasi: {selected_pit}")
    
    if not df_sump.empty:
        # A. KOMBINASI CHART: ELEVASI vs VOLUME
        st.subheader("Monitoring Elevasi & Volume")
        
        # Agregasi data jika All Sites dipilih
        chart_df = df_sump.groupby('Tanggal').agg({
            'Elevasi Air (m)': 'mean', 
            'Volume Air Survey (m3)': 'sum', 
            'Critical Elevation (m)': 'mean'
        }).reset_index()

        fig_combo = go.Figure()
        # Bar: Volume
        fig_combo.add_trace(go.Bar(
            x=chart_df['Tanggal'], y=chart_df['Volume Air Survey (m3)'],
            name='Volume Air (m³)', marker_color='lightblue', opacity=0.6, yaxis='y2'
        ))
        # Line: Elevasi
        fig_combo.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Elevasi Air (m)'],
            name='Elevasi (m)', mode='lines+markers', line=dict(color='blue', width=3)
        ))
        # Line: Critical
        fig_combo.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Critical Elevation (m)'],
            name='Critical Level', mode='lines', line=dict(color='red', width=2, dash='dash')
        ))
        
        fig_combo.update_layout(
            yaxis=dict(title="Elevasi (m)", side="left"),
            yaxis2=dict(title="Volume (m³)", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0)
        )
        st.plotly_chart(fig_combo, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Curah Hujan & Catchment")
        if not df_sump.empty:
            # Hitung Volume Hujan Masuk (Rain * Catchment)
            df_sump['Rain Volume (m3)'] = df_sump['Curah Hujan (mm)'] * df_sump['Actual Catchment (Ha)'] * 10
            
            fig_rain = px.bar(
                df_sump, x='Tanggal', y='Rain Volume (m3)', 
                title="Estimasi Volume Hujan Masuk (Catchment x CH)",
                labels={'Rain Volume (m3)': 'Volume Hujan (m³)'}
            )
            st.plotly_chart(fig_rain, use_container_width=True)
            
    with col2:
        st.subheader("Performa Pompa (Plan vs Actual)")
        if not df_pompa.empty:
            last_date = df_pompa['Tanggal'].max()
            df_last_pump = df_pompa[df_pompa['Tanggal'] == last_date]
            
            fig_pump = go.Figure()
            fig_pump.add_trace(go.Bar(
                x=df_last_pump['Unit Code'], y=df_last_pump['Debit Plan (m3/h)'],
                name='Plan Debit', marker_color='lightgrey'
            ))
            fig_pump.add_trace(go.Bar(
                x=df_last_pump['Unit Code'], y=df_last_pump['Debit Actual (m3/h)'],
                name='Actual Debit', marker_color='green'
            ))
            fig_pump.update_layout(barmode='group')
            st.plotly_chart(fig_pump, use_container_width=True)
