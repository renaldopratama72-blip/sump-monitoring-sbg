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

CRITICAL_LEVELS = {
    "Pit Wijaya Barat": 12.0, "Pit Wijaya Timur": 15.0,
    "Pit F01": 45.0, "Pit F02": 40.0, "Pit S8": 8.5
}

# --- 2. SETUP DATA DUMMY (DATA AWAL) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    
    for i in range(10): # Generate 10 hari data
        tgl = today - timedelta(days=i)
        
        for site, pit_list in SITE_MAP.items():
            for pit in pit_list:
                hujan = np.random.randint(0, 80) if i % 3 == 0 else 0
                catchment = 25.5 # Hektar (Dummy)
                gw_inflow = np.random.randint(50, 500) # Air tanah (Dummy)
                
                # Hitung Volume Masuk dari Hujan (Rumus simpel: mm * Ha * 10)
                rain_vol = hujan * catchment * 10 
                
                crit = CRITICAL_LEVELS.get(pit, 10.0)
                base_elev = crit - np.random.uniform(1, 4) 
                elevasi = base_elev + (hujan/50)
                vol_sump = int(elevasi * 5000) # Volume tampungan sump
                
                status = "BAHAYA" if elevasi > crit else "AMAN"
                
                data.append({
                    "Tanggal": tgl,
                    "Site": site,
                    "Pit": pit,
                    "Curah Hujan (mm)": float(hujan),
                    "Catchment Area (Ha)": catchment,
                    "Groundwater In (m3)": gw_inflow,
                    "Rain Volume (m3)": rain_vol, # Calculated
                    "Elevasi Aktual (m)": round(elevasi, 2),
                    "Critical Level (m)": crit,
                    "Volume Sump (m3)": vol_sump, 
                    "Status": status
                })
    
    df_initial = pd.DataFrame(data)
    df_initial = df_initial.sort_values(by=['Site', 'Pit', 'Tanggal'], ascending=[True, True, False])
    st.session_state.data_sump = df_initial

if 'data_pompa' not in st.session_state:
    # Dummy Data Pompa
    pump_data = []
    units = ["WP1203", "WP1005", "WP2001", "WP3001"]
    
    # Buat data pompa untuk setiap tanggal yg ada di data sump
    dates = st.session_state.data_sump['Tanggal'].unique()
    
    for d in dates:
        pump_data.append({
            "Tanggal": d, "Site": "Lais Coal Mine (LCM)", "Pit": "Pit Wijaya Barat", 
            "Unit Code": "WP1203", "Plan Debit (m3/h)": 500, "Actual Debit (m3/h)": np.random.randint(400, 500)
        })
        pump_data.append({
            "Tanggal": d, "Site": "Lais Coal Mine (LCM)", "Pit": "Pit Wijaya Timur", 
            "Unit Code": "WP1005", "Plan Debit (m3/h)": 300, "Actual Debit (m3/h)": np.random.randint(200, 300)
        })
        pump_data.append({
            "Tanggal": d, "Site": "Wiraduta Sejahtera Langgeng (WSL)", "Pit": "Pit F01", 
            "Unit Code": "WP2001", "Plan Debit (m3/h)": 400, "Actual Debit (m3/h)": np.random.randint(350, 400)
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

# Filter Dataframe
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# --- 4. HALAMAN DASHBOARD ---
if menu == "Dashboard Analisis":
    st.title(f"Dashboard: {selected_site}")
    if selected_pit != "All Pits":
        st.caption(f"Detail Analisis: {selected_pit}")
    
    # --- CHART 1: ELEVASI (Line) VS VOLUME (Bar) ---
    st.subheader("1. Monitoring Level & Volume Sump")
    if not df_sump.empty:
        # Kita ambil data pit spesifik atau rata-rata jika All Sites
        chart_df = df_sump.groupby('Tanggal').agg({
            'Elevasi Aktual (m)': 'mean', 'Volume Sump (m3)': 'sum', 'Critical Level (m)': 'mean'
        }).reset_index()

        fig_combo = go.Figure()
        
        # Bar Chart (Volume) - Sumbu Y Kanan (Secondary Y)
        fig_combo.add_trace(go.Bar(
            x=chart_df['Tanggal'], y=chart_df['Volume Sump (m3)'],
            name='Volume Air (m³)', marker_color='lightblue', opacity=0.6,
            yaxis='y2'
        ))
        
        # Line Chart (Elevasi) - Sumbu Y Kiri
        fig_combo.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Elevasi Aktual (m)'],
            name='Elevasi (m)', mode='lines+markers',
            line=dict(color='blue', width=3)
        ))

        # Line Chart (Critical)
        fig_combo.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Critical Level (m)'],
            name='Batas Kritis', mode='lines',
            line=dict(color='red', width=2, dash='dash')
        ))

        # Layout Dual Axis
        fig_combo.update_layout(
            yaxis=dict(title="Elevasi (meter)", side="left"),
            yaxis2=dict(title="Volume Air (m³)", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", y=1.1, x=0),
            hovermode="x unified"
        )
        st.plotly_chart(fig_combo, use_container_width=True)
    else:
        st.info("Pilih Pit spesifik untuk melihat grafik kombinasi.")

    col_A, col_B = st.columns(2)

    # --- CHART 2: DEBIT POMPA (PLAN VS ACTUAL) ---
    with col_A:
        st.subheader("2. Performa Pompa (Plan vs Actual)")
        if not df_pompa.empty:
            # Ambil data hari terakhir saja agar grafik tidak menumpuk
            last_date = df_pompa['Tanggal'].max()
            df_pump_last = df_pompa[df_pompa['Tanggal'] == last_date]
            
            fig_pump = go.Figure()
            
            # Bar Plan (Abu-abu)
            fig_pump.add_trace(go.Bar(
                x=df_pump_last['Unit Code'], y=df_pump_last['Plan Debit (m3/h)'],
                name='Plan Debit', marker_color='lightgrey'
            ))
            
            # Bar Actual (Warna sesuai site)
            fig_pump.add_trace(go.Bar(
                x=df_pump_last['Unit Code'], y=df_pump_last['Actual Debit (m3/h)'],
                name='Actual Debit', marker_color='#00CC96'
            ))
            
            fig_pump.update_layout(barmode='group', title=f"Debit Pompa Tanggal: {last_date}")
            st.plotly_chart(fig_pump, use_container_width=True)
        else:
            st.warning("Data pompa tidak tersedia.")

    # --- CHART 3: SUMBER AIR (RAIN VS GROUNDWATER) ---
    with col_B:
        st.subheader("3. Analisis Sumber Air Masuk")
        if not df_sump.empty:
            # Stacked Bar Chart
            # User minta catchment & groundwater. 
            # Kita visualisasikan Volume Air Hujan (Catchment * CH) vs Groundwater
            
            # Agregasi per tanggal
            df_hydro = df_sump.groupby('Tanggal')[['Rain Volume (m3)', 'Groundwater In (m3)']].sum().reset_index()
            
            fig_hydro = px.bar(
                df_hydro, x='Tanggal', y=['Rain Volume (m3)', 'Groundwater In (m3)'],
                title="Komposisi Inflow: Hujan vs Air Tanah",
                labels={'value': 'Volume Masuk (m³)', 'variable': 'Sumber Air'},
                color_discrete_map={'Rain Volume (m3)': '#636EFA', 'Groundwater In (m3)': '#FFA15A'}
            )
            st.plotly_chart(fig_hydro, use_container_width=True)

# --- 5. HALAMAN INPUT & EDIT ---
elif menu == "Input & Edit Data":
    st.title("📝 Input Data Harian")
    
    tab1, tab2 = st.tabs(["Data Sump (Hidrologi)", "Data Pompa (Mekanikal)"])
    
    with tab1:
        st.info("Edit data Catchment Area & Groundwater di sini.")
        
        # Kolom Config untuk Data Editor
        sump_config = {
            "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys()), required=True),
            "Pit": st.column_config.SelectboxColumn(options=["Pit Wijaya Barat", "Pit Wijaya Timur", "Pit F01", "Pit F02", "Pit S8"], required=True),
            "Tanggal": st.column_config.DateColumn(format="DD/MM/YYYY"),
            "Curah Hujan (mm)": st.column_config.NumberColumn(format="%.1f mm"),
            "Catchment Area (Ha)": st.column_config.NumberColumn(help="Luas daerah tangkapan hujan"),
            "Groundwater In (m3)": st.column_config.NumberColumn(help="Estimasi air tanah masuk"),
            "Volume Sump (m3)": st.column_config.NumberColumn(format="%d m³"),
            "Status": st.column_config.TextColumn(disabled=True)
        }
        
        edited_sump = st.data_editor(
            df_sump, 
            num_rows="dynamic", use_container_width=True,
            column_config=sump_config,
            key="editor_sump"
        )
        
        if st.button("Simpan Data Sump"):
            # Update data session
            st.session_state.data_sump = edited_sump
            
            # Recalculate Logic (Rain Volume)
            # Karena ini dataframe pandas, kita bisa hitung ulang kolom Rain Volume
            st.session_state.data_sump['Rain Volume (m3)'] = (
                st.session_state.data_sump['Curah Hujan (mm)'] * st.session_state.data_sump['Catchment Area (Ha)'] * 10
            )
            
            st.session_state.data_sump['Status'] = np.where(
                st.session_state.data_sump['Elevasi Aktual (m)'] > st.session_state.data_sump['Critical Level (m)'], 
                'BAHAYA', 'AMAN'
            )
            st.success("Data Hidrologi Tersimpan & Dihitung Ulang!")
            st.rerun()

    with tab2:
        st.info("Edit Plan vs Actual Pompa di sini.")
        
        pump_config = {
             "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys())),
             "Pit": st.column_config.SelectboxColumn(options=["Pit Wijaya Barat", "Pit Wijaya Timur", "Pit F01", "Pit F02", "Pit S8"]),
             "Plan Debit (m3/h)": st.column_config.NumberColumn(format="%d"),
             "Actual Debit (m3/h)": st.column_config.NumberColumn(format="%d")
        }
        
        edited_pompa = st.data_editor(
            df_pompa,
            num_rows="dynamic", use_container_width=True,
            column_config=pump_config,
            key="editor_pompa"
        )
        
        if st.button("Simpan Data Pompa"):
            st.session_state.data_pompa = edited_pompa
            st.success("Data Pompa Tersimpan!")
            st.rerun()
