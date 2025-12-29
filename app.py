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

# --- CONFIG SITE & PIT (DATA REAL) ---
# Struktur Hierarki: Site -> List of Pits
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# Dummy Critical Levels per Pit (Bisa diedit user nanti)
CRITICAL_LEVELS = {
    "Pit Wijaya Barat": 12.0,
    "Pit Wijaya Timur": 15.0,
    "Pit F01": 45.0,
    "Pit F02": 40.0,
    "Pit S8": 8.5
}

# --- 2. SETUP DATA DUMMY (SIMULASI DATABASE) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    
    # Generate data mundur 7 hari untuk SETIAP Pit di SETIAP Site
    for i in range(7):
        tgl = today - timedelta(days=i)
        
        for site, pit_list in SITE_MAP.items():
            for pit in pit_list:
                # Randomizer data agar terlihat beda-beda tiap pit
                hujan = np.random.randint(0, 60) if i % 3 == 0 else 0
                crit = CRITICAL_LEVELS.get(pit, 10.0)
                
                # Logic Elevasi dummy
                base_elev = crit - np.random.uniform(1, 3) 
                elevasi = base_elev + (hujan/40) 
                
                status = "BAHAYA" if elevasi > crit else "AMAN"
                
                data.append({
                    "Tanggal": tgl,
                    "Site": site,
                    "Pit": pit,
                    "Curah Hujan (mm)": float(hujan),
                    "Elevasi Aktual (m)": round(elevasi, 2),
                    "Critical Level (m)": crit,
                    "Volume Air (m3)": int(elevasi * 2500), 
                    "Status": status
                })
    
    df_initial = pd.DataFrame(data)
    df_initial = df_initial.sort_values(by=['Site', 'Pit', 'Tanggal'], ascending=[True, True, False])
    st.session_state.data_sump = df_initial

if 'data_pompa' not in st.session_state:
    # Template data pompa dummy
    st.session_state.data_pompa = pd.DataFrame({
        "Tanggal": [date.today()] * 4,
        "Site": ["Lais Coal Mine (LCM)", "Lais Coal Mine (LCM)", "Wiraduta Sejahtera Langgeng (WSL)", "Nusantara Energy (NE)"],
        "Pit": ["Pit Wijaya Barat", "Pit Wijaya Timur", "Pit F01", "Pit S8"], # Lokasi Pompa
        "Unit Code": ["WP1203", "WP1005", "WP2001", "WP3001"],
        "Plan Flowrate (m3/h)": [500, 300, 380, 500],
        "Actual Flowrate (m3/h)": [450, 280, 300, 480],
        "HM Start": [1000.0, 500.0, 2000.0, 5000.0],
        "HM End": [1010.0, 510.0, 2012.0, 5008.0]
    })

# --- 3. SIDEBAR NAVIGASI ---
st.sidebar.title("🌊 Sump Monitor")
menu = st.sidebar.radio("Menu Utama:", ["Dashboard Monitoring", "Input & Edit Data"])

st.sidebar.divider()
st.sidebar.subheader("Filter Lokasi")

# Filter Level 1: Site
selected_site = st.sidebar.selectbox("Pilih Site:", ["All Sites"] + list(SITE_MAP.keys()))

# Filter Level 2: Pit (Muncul otomatis sesuai Site yang dipilih)
selected_pit = "All Pits"
if selected_site != "All Sites":
    available_pits = ["All Pits"] + SITE_MAP[selected_site]
    selected_pit = st.sidebar.selectbox("Pilih Pit:", available_pits)

# --- FILTER LOGIC ---
df_sump = st.session_state.data_sump
df_pompa = st.session_state.data_pompa

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

# --- 4. HALAMAN UTAMA: DASHBOARD ---
if menu == "Dashboard Monitoring":
    st.title(f"Dashboard: {selected_site}")
    if selected_site != "All Sites":
        st.caption(f"Area Fokus: {selected_pit}")
    
    # --- TOP METRICS ---
    # Mengambil rata-rata atau total dari data yang difilter
    if not df_sump.empty:
        # Ambil data tanggal terakhir saja untuk KPI
        latest_date = df_sump['Tanggal'].max()
        df_latest = df_sump[df_sump['Tanggal'] == latest_date]
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_vol = df_latest['Volume Air (m3)'].sum()
        avg_rain = df_latest['Curah Hujan (mm)'].mean()
        danger_count = len(df_latest[df_latest['Status'] == 'BAHAYA'])
        
        status_global = "AMAN" if danger_count == 0 else f"BAHAYA ({danger_count} Pit)"
        status_color = "green" if danger_count == 0 else "red"

        with col1:
            st.markdown(f"### Status Site: :{status_color}[{status_global}]")
        with col2:
            st.metric("Rata-rata Hujan (Hari Ini)", f"{avg_rain:.1f} mm")
        with col3:
            st.metric("Total Volume Air", f"{total_vol:,.0f} m³")
        with col4:
            st.metric("Jumlah Pit Terpantau", f"{len(df_latest)} Pit")
    
    st.divider()

    # --- GRAFIK TREN ELEVASI ---
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Tren Elevasi Air")
        if not df_sump.empty:
            # Grafik Multi-Line (Setiap Garis adalah Satu Pit)
            fig = px.line(df_sump, x='Tanggal', y='Elevasi Aktual (m)', color='Pit', markers=True,
                          title="Pergerakan Air per Pit")
            # Menambah garis batas kritis (hanya jika 1 pit dipilih agar tidak pusing)
            if selected_pit != "All Pits" and selected_site != "All Sites":
                crit_val = df_sump['Critical Level (m)'].iloc[0]
                fig.add_hline(y=crit_val, line_dash="dash", line_color="red", annotation_text="Batas Kritis")
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Tidak ada data untuk ditampilkan.")

    with c2:
        st.subheader("Efisiensi Pompa")
        if not df_pompa.empty:
            df_pompa['Eff'] = (df_pompa['Actual Flowrate (m3/h)'] / df_pompa['Plan Flowrate (m3/h)']) * 100
            fig_pump = px.bar(df_pompa, x='Unit Code', y='Eff', color='Pit', 
                              color_discrete_sequence=px.colors.qualitative.Bold,
                              labels={'Eff': 'Efisiensi (%)'})
            st.plotly_chart(fig_pump, use_container_width=True)
        else:
            st.warning("Data pompa kosong.")

# --- 5. HALAMAN INPUT & EDIT (EXCEL STYLE) ---
elif menu == "Input & Edit Data":
    st.title("📝 Input Data Harian")
    st.markdown("Silakan edit data langsung pada tabel. **Data otomatis tersimpan.**")
    
    tab1, tab2 = st.tabs(["Data Sump (Air)", "Data Pompa (Unit)"])
    
    with tab1:
        st.info(f"Mengedit Data Sump untuk: **{selected_site}**")
        
        # Konfigurasi Kolom agar user mudah memilih Pit yang benar
        all_pits_list = []
        for s in SITE_MAP.values():
            all_pits_list.extend(s)

        edited_sump = st.data_editor(
            df_sump, # Hanya menampilkan data yang sedang difilter
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys()), required=True),
                "Pit": st.column_config.SelectboxColumn(options=all_pits_list, required=True),
                "Tanggal": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Status": st.column_config.TextColumn(disabled=True)
            },
            key="editor_sump"
        )
        
        if st.button("Simpan Data Sump"):
            # Update logic (Di real app ini akan UPDATE ke SQL Database)
            st.session_state.data_sump.update(edited_sump)
            
            # Recalculate Status
            st.session_state.data_sump['Status'] = np.where(
                st.session_state.data_sump['Elevasi Aktual (m)'] > st.session_state.data_sump['Critical Level (m)'], 
                'BAHAYA', 'AMAN'
            )
            st.success("Data berhasil diupdate!")
            st.rerun()

    with tab2:
        st.info(f"Mengedit Data Pompa untuk: **{selected_site}**")
        edited_pompa = st.data_editor(
            df_pompa,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                 "Site": st.column_config.SelectboxColumn(options=list(SITE_MAP.keys())),
                 "Pit": st.column_config.SelectboxColumn(options=all_pits_list),
            },
            key="editor_pompa"
        )
        
        if st.button("Simpan Data Pompa"):
            st.session_state.data_pompa.update(edited_pompa)
            st.success("Data Pompa berhasil diupdate!")
            st.rerun()
