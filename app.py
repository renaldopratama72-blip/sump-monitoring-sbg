import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np

# --- 1. SETUP & UI CONFIG ---
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
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .stDownloadButton button {
        background-color: #2c3e50; color: white; border-radius: 8px; height: 50px; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# CONFIG SITE
SITE_MAP = {
    "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
    "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
    "Nusantara Energy (NE)": ["Pit S8"]
}

# --- 2. DATA GENERATOR (DUMMY) ---
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0] 
            hujan = np.random.choice([0, 0, 0, 0, 35, 12, 5, 60])
            elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
            data.append({
                "Tanggal": pd.to_datetime(d), 
                "Site": site, "Pit": pit,
                "Elevasi Air (m)": round(elev, 2), 
                "Critical Elevation (m)": 13.0,
                "Volume Air Survey (m3)": int(elev * 500), 
                "Curah Hujan (mm)": hujan,
                "Actual Catchment (Ha)": 25.0, 
                "Status": "BAHAYA" if elev > 13.0 else "AMAN"
            })
    st.session_state.data_sump = pd.DataFrame(data)

if 'data_pompa' not in st.session_state:
    data_p = []
    today = date.today()
    units = ["WP-01", "WP-02"] 
    for i in range(120):
        d = today - timedelta(days=i)
        for site in SITE_MAP.keys():
            pit = SITE_MAP[site][0]
            for u in units:
                hm = np.random.uniform(10, 22) if u == "WP-01" else np.random.uniform(5, 15)
                debit_act = np.random.randint(400, 480) if u == "WP-01" else np.random.randint(200, 300)
                data_p.append({
                    "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                    "Unit Code": u, 
                    "Debit Plan (m3/h)": 500 if u == "WP-01" else 350, 
                    "Debit Actual (m3/h)": debit_act, 
                    "EWH": round(hm, 1)
                })
    st.session_state.data_pompa = pd.DataFrame(data_p)

st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🌊 Water Management")
    st.caption("FILTER LOKASI")
    selected_site = st.selectbox("📍 Site Area", ["All Sites"] + list(SITE_MAP.keys()))
    pit_options = ["All Pits"]
    if selected_site != "All Sites": pit_options += SITE_MAP[selected_site]
    selected_pit = st.selectbox("⛏️ Pit Area", pit_options)
    
    st.caption("FILTER PERIODE")
    available_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    selected_year = st.selectbox("📅 Tahun", available_years)
    
    month_map = {1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
                 7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"}
    current_month_idx = date.today().month - 1
    selected_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=current_month_idx)
    selected_month_int = [k for k, v in month_map.items() if v == selected_month_name][0]

# --- FILTER LOGIC ---
df_sump = st.session_state.data_sump.copy()
df_pompa = st.session_state.data_pompa.copy()

if selected_site != "All Sites":
    df_sump = df_sump[df_sump['Site'] == selected_site]
    df_pompa = df_pompa[df_pompa['Site'] == selected_site]
    if selected_pit != "All Pits":
        df_sump = df_sump[df_sump['Pit'] == selected_pit]
        df_pompa = df_pompa[df_pompa['Pit'] == selected_pit]

df_sump_filtered = df_sump[
    (df_sump['Tanggal'].dt.year == selected_year) & 
    (df_sump['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

df_pompa_filtered = df_pompa[
    (df_pompa['Tanggal'].dt.year == selected_year) & 
    (df_pompa['Tanggal'].dt.month == selected_month_int)
].sort_values(by="Tanggal")

# --- 4. TABS ---
tab_dash, tab_input, tab_db = st.tabs(["📊 Dashboard Executive", "📝 Input Data", "📂 Download Center"])

with tab_dash:
    st.title(f"{selected_month_name} {selected_year}")
    st.markdown(f"**Site:** {selected_site} | **Pit:** {selected_pit}")
    
    if df_sump_filtered.empty:
        st.warning("⚠️ Data belum tersedia.")
    else:
        # A. KARTU METRIK
        last_entry = df_sump_filtered.iloc[-1] 
        total_rain = df_sump_filtered['Curah Hujan (mm)'].sum()
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Elevasi Akhir", f"{last_entry['Elevasi Air (m)']} m", f"Limit: {last_entry['Critical Elevation (m)']} m", delta_color="off")
        with c2: st.metric("Volume Air", f"{last_entry['Volume Air Survey (m3)']:,.0f} m³")
        with c3: st.metric("Total Hujan", f"{total_rain:.1f} mm")
        with c4:
            clr = "#e74c3c" if last_entry['Status'] == "BAHAYA" else "#27ae60"
            st.markdown(f"<div style='background-color:{clr}; color:white; padding:10px; border-radius:8px; text-align:center;'><b>{last_entry['Status']}</b></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # B. GRAFIK UTAMA (DENGAN DATA LABELS)
        c_left, c_right = st.columns([2, 1])
        
        with c_left:
            st.markdown("### 📈 Tren Hidrologi Harian")
            chart_sump = df_sump_filtered.groupby('Tanggal').agg({
                'Elevasi Air (m)': 'mean', 'Volume Air Survey (m3)': 'sum', 'Critical Elevation (m)': 'mean'
            }).reset_index()

            fig = go.Figure()
            # Bar Volume (Label format: 5k, 10k untuk hemat tempat)
            fig.add_trace(go.Bar(
                x=chart_sump['Tanggal'], y=chart_sump['Volume Air Survey (m3)'], 
                name='Volume', marker_color='#d6eaf8', opacity=0.8, yaxis='y2',
                text=chart_sump['Volume Air Survey (m3)'],
                texttemplate='%{text:.2s}', textposition='auto' # Label Volume
            ))
            # Line Elevasi (Label format: 12.55)
            fig.add_trace(go.Scatter(
                x=chart_sump['Tanggal'], y=chart_sump['Elevasi Air (m)'], 
                name='Elevasi', mode='lines+markers+text',
                line=dict(color='#2980b9', width=3),
                text=chart_sump['Elevasi Air (m)'],
                texttemplate='%{text:.2f}', textposition='top center', # Label Elevasi
                textfont=dict(size=10, color='#2980b9')
            ))
            # Line Critical
            fig.add_trace(go.Scatter(
                x=chart_sump['Tanggal'], y=chart_sump['Critical Elevation (m)'], 
                name='Critical', line=dict(color='#e74c3c', dash='dash')
            ))
            
            fig.update_layout(
                yaxis=dict(title="Elevasi (m)", side="left"),
                yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
                xaxis=dict(tickformat="%d", title="Tanggal", showgrid=False),
                legend=dict(orientation="h", y=1.1, x=0),
                height=450, margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.markdown("### 🌧️ Curah Hujan")
            # Bar Hujan dengan Label
            fig_rain = go.Figure()
            fig_rain.add_trace(go.Bar(
                x=df_sump_filtered['Tanggal'], 
                y=df_sump_filtered['Curah Hujan (mm)'],
                marker_color='#34495e',
                text=df_sump_filtered['Curah Hujan (mm)'],
                texttemplate='%{text}', textposition='outside' # Label Hujan
            ))
            fig_rain.update_layout(
                xaxis=dict(tickformat="%d", title=None),
                yaxis=dict(title="mm"), height=450,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_rain, use_container_width=True)

        # C. DETAIL POMPA (DENGAN LABELS)
        st.markdown("### ⚙️ Analisis Performa Pompa")
        
        if not df_pompa_filtered.empty:
            unit_list = df_pompa_filtered['Unit Code'].unique()
            selected_unit_graph = st.selectbox("Pilih Unit:", unit_list, label_visibility="collapsed")
            
            df_pump_daily = df_pompa_filtered[df_pompa_filtered['Unit Code'] == selected_unit_graph].sort_values(by="Tanggal")
            
            fig_p_day = go.Figure()
            # Bar Debit (Label)
            fig_p_day.add_trace(go.Bar(
                x=df_pump_daily['Tanggal'], y=df_pump_daily['Debit Actual (m3/h)'],
                name='Debit Actual', marker_color='#27ae60',
                text=df_pump_daily['Debit Actual (m3/h)'],
                textposition='inside', textfont=dict(color='white')
            ))
            # Line EWH (Label)
            fig_p_day.add_trace(go.Scatter(
                x=df_pump_daily['Tanggal'], y=df_pump_daily['EWH'],
                name='EWH (Jam)', mode='lines+markers+text',
                marker=dict(size=8, color='#f39c12'),
                line=dict(width=3, color='#f39c12'), yaxis='y2',
                text=df_pump_daily['EWH'],
                texttemplate='%{text:.1f}', textposition='top center',
                textfont=dict(color='#d35400')
            ))

            fig_p_day.update_layout(
                yaxis=dict(title="Flowrate (m3/h)", showgrid=True),
                yaxis2=dict(title="EWH (Jam)", overlaying="y", side="right", showgrid=False, range=[0, 26]),
                xaxis=dict(tickformat="%d %b", dtick="D1", showgrid=False),
                legend=dict(orientation="h", y=1.1),
                height=400
            )
            st.plotly_chart(fig_p_day, use_container_width=True)

# TAB 2: INPUT
with tab_input:
    st.subheader("📝 Form Input Data")
    with st.container():
        c_date, c_site, c_pit = st.columns(3)
        date_in = c_date.date_input("Tanggal", date.today())
        site_in = c_site.selectbox("Site", list(SITE_MAP.keys()), key="s_in")
        pit_in = c_pit.selectbox("Pit", SITE_MAP[site_in], key="p_in")
    st.markdown("---")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### 1. Data Sump")
        with st.form("f_sump"):
            c1, c2 = st.columns(2)
            e_act = c1.number_input("Elevasi (m)", format="%.2f")
            e_crit = c2.number_input("Critical (m)", value=12.0)
            vol = c1.number_input("Volume (m3)", step=100)
            catch = c2.number_input("Catchment (Ha)", format="%.2f")
            rain = st.number_input("Hujan (mm)", format="%.1f")
            if st.form_submit_button("Simpan Sump", use_container_width=True):
                st.session_state.data_sump = pd.concat([pd.DataFrame([{
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                    "Volume Air Survey (m3)": vol, "Curah Hujan (mm)": rain,
                    "Actual Catchment (Ha)": catch, "Status": "BAHAYA" if e_act > e_crit else "AMAN"
                }]), st.session_state.data_sump], ignore_index=True)
                st.success("Tersimpan!")
    with col_r:
        st.markdown("#### 2. Data Pompa")
        with st.form("f_pump"):
            u_code = st.text_input("Kode Unit")
            c3, c4 = st.columns(2)
            d_plan = c3.number_input("Debit Plan", value=500)
            d_act = c4.number_input("Debit Actual", value=450)
            ewh_in = st.number_input("EWH", max_value=24.0, format="%.1f")
            if st.form_submit_button("Simpan Pompa", use_container_width=True):
                st.session_state.data_pompa = pd.concat([pd.DataFrame([{
                    "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                    "Unit Code": u_code, "Debit Plan (m3/h)": d_plan,
                    "Debit Actual (m3/h)": d_act, "EWH": ewh_in
                }]), st.session_state.data_pompa], ignore_index=True)
                st.success("Tersimpan!")

# TAB 3: DOWNLOAD (GABUNGAN)
with tab_db:
    st.subheader("📂 Download Center")
    dl_site = st.selectbox("Pilih Site:", list(SITE_MAP.keys()))
    df_s_raw = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
    df_p_raw = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
    
    if not df_s_raw.empty:
        df_combined = pd.merge(df_s_raw, df_p_raw, on=['Tanggal', 'Site', 'Pit'], how='outer', suffixes=('_Sump', '_Pompa'))
        df_combined = df_combined.sort_values(by=['Tanggal', 'Pit', 'Unit Code'])
        st.dataframe(df_combined.head(3), use_container_width=True)
        st.download_button("⬇️ DOWNLOAD FULL REPORT (CSV)", df_combined.to_csv(index=False).encode('utf-8'), f"Master_{dl_site}.csv", "text/csv")
    else:
        st.warning("Data kosong.")
