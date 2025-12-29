import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Mining Water Management",
    page_icon="🌊",
    layout="wide"
)

# --- CONFIG SITE & PIT ---
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# --- 2. SETUP DATABASE SEMENTARA (SESSION STATE) ---
if 'data_sump' not in st.session_state:
    # Data dummy awal (kosongkan jika mau bersih)
    data = []
    # Kita isi sedikit sample agar dashboard tidak error saat pertama buka
    today = date.today()
    data.append({
        "Tanggal": today,
        "Site": "Lais Coal Mine (LCM)",
        "Pit": "Pit Wijaya Barat",
        "Elevasi Air (m)": 11.5,
        "Critical Elevation (m)": 12.0,
        "Volume Air Survey (m3)": 5000,
        "Curah Hujan (mm)": 12.0,
        "Actual Catchment (Ha)": 25.0,
        "Status": "AMAN"
    })
    st.session_state.data_sump = pd.DataFrame(data)

if 'data_pompa' not in st.session_state:
    st.session_state.data_pompa = pd.DataFrame(columns=[
        "Tanggal", "Site", "Pit", "Unit Code", 
        "Debit Plan (m3/h)", "Debit Actual (m3/h)", "HM Running"
    ])

# --- 3. SIDEBAR MENU ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2942/2942076.png", width=50) # Logo Placeholder
st.sidebar.title("Sump Monitor")
menu = st.sidebar.radio("Menu:", ["Dashboard Utama", "Input Data Harian"])

st.sidebar.divider()
st.sidebar.caption("Filter Dashboard:")
selected_site = st.sidebar.selectbox("Pilih Site:", ["All Sites"] + list(SITE_MAP.keys()))

selected_pit = "All Pits"
if selected_site != "All Sites":
    selected_pit = st.sidebar.selectbox("Pilih Pit:", ["All Pits"] + SITE_MAP[selected_site])

# --- 4. MENU INPUT DATA (FORM STYLE) ---
if menu == "Input Data Harian":
    st.title("📝 Input Data Harian")
    st.markdown("Silakan isi formulir di bawah ini dan tekan tombol **Simpan**.")

    # --- BAGIAN A: PILIH LOKASI & TANGGAL ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            in_date = st.date_input("Tanggal Data", date.today())
        with c2:
            in_site = st.selectbox("Site", list(SITE_MAP.keys()), key="in_site")
        with c3:
            # Pit menyesuaikan Site
            in_pit = st.selectbox("Pit", SITE_MAP[in_site], key="in_pit")

    st.divider()

    # --- BAGIAN B: FORMULIR DATA SUMP ---
    col_form1, col_form2 = st.columns([1, 1])
    
    with col_form1:
        st.subheader("1. Data Sump (Air)")
        with st.form("form_sump"):
            st.caption("Isi data elevasi dan hidrologi:")
            
            f_elev = st.number_input("1. Elevasi Air Aktual (m)", min_value=0.0, format="%.2f")
            f_crit = st.number_input("2. Critical Elevation (m)", min_value=0.0, value=12.0, format="%.2f")
            f_vol  = st.number_input("3. Volume Air Survey (m3)", min_value=0, step=100)
            f_rain = st.number_input("4. Curah Hujan (mm)", min_value=0.0, format="%.1f")
            f_catch = st.number_input("5. Actual Catchment (Ha)", min_value=0.0, format="%.2f")
            
            # TOMBOL SIMPAN
            btn_sump = st.form_submit_button("💾 SIMPAN DATA SUMP", type="primary")
            
            if btn_sump:
                # LOGIKA AMAN / BAHAYA
                if f_elev > f_crit:
                    status_cek = "BAHAYA"
                else:
                    status_cek = "AMAN"
                
                # Simpan ke Database (Session State)
                new_sump = {
                    "Tanggal": in_date,
                    "Site": in_site,
                    "Pit": in_pit,
                    "Elevasi Air (m)": f_elev,
                    "Critical Elevation (m)": f_crit,
                    "Volume Air Survey (m3)": f_vol,
                    "Curah Hujan (mm)": f_rain,
                    "Actual Catchment (Ha)": f_catch,
                    "Status": status_cek
                }
                st.session_state.data_sump = pd.concat([pd.DataFrame([new_sump]), st.session_state.data_sump], ignore_index=True)
                
                if status_cek == "BAHAYA":
                    st.error(f"Data Tersimpan! Status: BAHAYA (Elevasi {f_elev} > Critical {f_crit})")
                else:
                    st.success("Data Tersimpan! Status: AMAN.")

    # --- BAGIAN C: FORMULIR DATA POMPA ---
    with col_form2:
        st.subheader("2. Data Pompa (Unit)")
        with st.form("form_pompa"):
            st.caption("Input performa unit pompa:")
            
            p_unit = st.text_input("Kode Unit (Contoh: WP1203)")
            p_plan = st.number_input("Debit Plan (m3/h)", min_value=0)
            p_act  = st.number_input("Debit Actual (m3/h)", min_value=0)
            p_hm   = st.number_input("Jam Jalan / HM Running", min_value=0.0, format="%.1f")
            
            # TOMBOL SIMPAN
            btn_pompa = st.form_submit_button("💾 SIMPAN DATA POMPA")
            
            if btn_pompa:
                if p_unit == "":
                    st.warning("Harap isi Kode Unit!")
                else:
                    new_pump = {
                        "Tanggal": in_date,
                        "Site": in_site,
                        "Pit": in_pit,
                        "Unit Code": p_unit,
                        "Debit Plan (m3/h)": p_plan,
                        "Debit Actual (m3/h)": p_act,
                        "HM Running": p_hm
                    }
                    st.session_state.data_pompa = pd.concat([pd.DataFrame([new_pump]), st.session_state.data_pompa], ignore_index=True)
                    st.success(f"Unit {p_unit} berhasil disimpan!")

    st.divider()
    
    # --- TABEL HASIL INPUT (UNTUK CEK) ---
    with st.expander("Lihat Data yang Sudah Diinput Hari Ini"):
        df_today = st.session_state.data_sump[st.session_state.data_sump['Tanggal'] == in_date]
        st.dataframe(df_today, use_container_width=True)

# --- 5. MENU DASHBOARD ---
elif menu == "Dashboard Utama":
    # Filter Data
    df_sump = st.session_state.data_sump.copy()
    df_pompa = st.session_state.data_pompa.copy()
    
    if selected_site != "All Sites":
        df_sump = df_sump[df_sump['Site'] == selected_site]
        df_pompa = df_pompa[df_pompa['Site'] == selected_site]
        if selected_pit != "All Pits":
            df_sump = df_sump[df_sump['Pit'] == selected_pit]
            df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

    st.title(f"Dashboard Monitor: {selected_site}")
    
    if df_sump.empty:
        st.warning("Belum ada data inputan untuk filter ini.")
    else:
        # A. KARTU STATUS TERKINI
        # Ambil data paling baru berdasarkan tanggal input
        latest_entry = df_sump.sort_values(by="Tanggal", ascending=False).iloc[0]
        
        c1, c2, c3, c4 = st.columns(4)
        
        status_now = latest_entry['Status']
        # Logic Warna Kartu
        color_status = "red" if status_now == "BAHAYA" else "green"
        
        with c1:
            st.markdown(f"### Status: :{color_status}[{status_now}]")
            st.caption(f"Update: {latest_entry['Tanggal']}")
        with c2:
            st.metric("Elevasi Aktual", f"{latest_entry['Elevasi Air (m)']} m")
            st.caption(f"Batas Kritis: {latest_entry['Critical Elevation (m)']} m")
        with c3:
            st.metric("Volume Air", f"{latest_entry['Volume Air Survey (m3)']:,.0f} m³")
        with c4:
            st.metric("Curah Hujan", f"{latest_entry['Curah Hujan (mm)']} mm")
            
        st.divider()
        
        # B. GRAFIK UTAMA (DUAL AXIS)
        st.subheader("Grafik Elevasi vs Volume")
        
        # Urutkan data berdasarkan tanggal untuk grafik
        chart_df = df_sump.sort_values(by="Tanggal")
        
        fig = go.Figure()
        
        # Bar: Volume
        fig.add_trace(go.Bar(
            x=chart_df['Tanggal'], y=chart_df['Volume Air Survey (m3)'],
            name='Volume (m3)', marker_color='lightblue', opacity=0.5, yaxis='y2'
        ))
        
        # Line: Critical Level (Batas)
        fig.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Critical Elevation (m)'],
            name='Critical Level', mode='lines', 
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Line: Elevasi Aktual
        fig.add_trace(go.Scatter(
            x=chart_df['Tanggal'], y=chart_df['Elevasi Air (m)'],
            name='Elevasi Aktual', mode='lines+markers',
            line=dict(color='blue', width=3)
        ))
        
        # Layout
        fig.update_layout(
            yaxis=dict(title="Elevasi (m)", side="left"),
            yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
            hovermode="x unified",
            legend=dict(orientation="h", y=1.1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # C. DATA POMPA
        st.subheader("Performa Pompa (Plan vs Actual)")
        if not df_pompa.empty:
            # Grouping jika ada banyak unit, ambil data terbaru
            fig_pump = px.bar(
                df_pompa, x="Unit Code", y=["Debit Plan (m3/h)", "Debit Actual (m3/h)"],
                barmode="group",
                color_discrete_map={"Debit Plan (m3/h)": "grey", "Debit Actual (m3/h)": "green"},
                title="Perbandingan Debit Pompa"
            )
            st.plotly_chart(fig_pump, use_container_width=True)
        else:
            st.info("Belum ada data pompa yang diinput.")
