import streamlit as st
import pandas as pd
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

# --- 2. INITIALIZE SESSION STATE (DATABASE SEMENTARA) ---

# A. DATA LOGIN (Username: admin, Password: admin123)
USERS = {
    "admin": "admin123",
    "site_lcm": "lcm2024",
    "site_wsl": "wsl2024"
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# B. DYNAMIC SITE MAP (Agar bisa ditambah)
if 'site_map' not in st.session_state:
    st.session_state['site_map'] = {
        "Lais Coal Mine (LCM)": ["Pit Wijaya Barat", "Pit Wijaya Timur"],
        "Wiraduta Sejahtera Langgeng (WSL)": ["Pit F01", "Pit F02"],
        "Nusantara Energy (NE)": ["Pit S8"]
    }

# C. DATA DUMMY GENERATOR
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    # Gunakan site_map dari session_state
    current_map = st.session_state['site_map']
    
    for i in range(120):
        d = today - timedelta(days=i)
        for site in current_map.keys():
            # Cek jika site punya pit
            if len(current_map[site]) > 0:
                pit = current_map[site][0] 
                # Hujan
                rain_plan = np.random.choice([10, 20, 30, 40])
                rain_act = np.random.choice([0, 0, 0, 5, 15, 45, 60, 10])
                
                # Elevasi & Volume
                elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
                vol = int(elev * 5000) 
                
                data.append({
                    "Tanggal": pd.to_datetime(d), 
                    "Site": site, "Pit": pit,
                    "Elevasi Air (m)": round(elev, 2), 
                    "Critical Elevation (m)": 13.0,
                    "Volume Air Survey (m3)": vol,
                    "Plan Curah Hujan (mm)": rain_plan,   
                    "Curah Hujan (mm)": rain_act,         
                    "Actual Catchment (Ha)": 25.0, 
                    "Status": "BAHAYA" if elev > 13.0 else "AMAN"
                })
    st.session_state.data_sump = pd.DataFrame(data).sort_values(by=["Site", "Pit", "Tanggal"])

if 'data_pompa' not in st.session_state:
    data_p = []
    today = date.today()
    units = ["WP-01", "WP-02"]
    current_map = st.session_state['site_map']
    
    for i in range(120):
        d = today - timedelta(days=i)
        for site in current_map.keys():
            if len(current_map[site]) > 0:
                pit = current_map[site][0]
                for u in units:
                    ewh_plan = 20.0
                    ewh_act = np.random.uniform(15, 22)
                    d_plan = 500
                    d_act = np.random.randint(400, 480)
                    data_p.append({
                        "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                        "Unit Code": u, 
                        "Debit Plan (m3/h)": d_plan, "Debit Actual (m3/h)": d_act, 
                        "EWH Plan": ewh_plan, "EWH Actual": round(ewh_act, 1)
                    })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Ensure types
st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. FUNGSI LOGIN ---
def check_login():
    username = st.session_state['input_user']
    password = st.session_state['input_pass']
    
    if username in USERS and USERS[username] == password:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.success("Login Berhasil!")
    else:
        st.error("Username atau Password Salah!")

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    # Rerun workaround
    st.rerun()

# ==============================================================================
# MAIN APP LOGIC
# ==============================================================================

if not st.session_state['logged_in']:
    # TAMPILAN HALAMAN LOGIN
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.title("🔐 Water Management Login")
        st.markdown("Silakan login untuk mengakses dashboard.")
        st.text_input("Username", key="input_user")
        st.text_input("Password", type="password", key="input_pass")
        st.button("LOGIN MASUK", on_click=check_login)
        
        st.info("Demo Account -> User: **admin**, Pass: **admin123**")

else:
    # TAMPILAN SETELAH LOGIN (KODE LAMA DIMASUKKAN KE SINI)
    
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🌊 Water Control")
        st.write(f"Halo, **{st.session_state['username']}**")
        if st.button("Log Out"):
            logout()
            
        st.divider()
        
        # Menggunakan variable site_map dari session_state
        current_sites = list(st.session_state['site_map'].keys())
        selected_site = st.selectbox("📍 Site", ["All Sites"] + current_sites)
        
        pit_options = ["All Pits"]
        if selected_site != "All Sites": 
            pit_options += st.session_state['site_map'][selected_site]
        selected_pit = st.selectbox("⛏️ Pit", pit_options)
        
        st.caption("FILTER WAKTU")
        avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
        sel_year = st.selectbox("📅 Tahun", avail_years)
        month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
        curr_m = date.today().month
        sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
        sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

    # --- CALCULATION ENGINE ---
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

    # --- WATER BALANCE LOGIC ---
    df_p_daily = df_p.copy()
    df_p_daily['Volume Out'] = df_p_daily['Debit Actual (m3/h)'] * df_p_daily['EWH Actual']
    daily_out = df_p_daily.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()

    df_wb = pd.merge(df_s, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
    df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)
    df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
    df_wb = df_wb.sort_values(by=['Site', 'Pit', 'Tanggal'])
    df_wb['Volume Kemarin'] = df_wb.groupby(['Site', 'Pit'])['Volume Air Survey (m3)'].shift(1)
    df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] - df_wb['Volume Out']
    df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
    df_wb['Error %'] = (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100

    df_wb_dash = df_wb[
        (df_wb['Tanggal'].dt.year == sel_year) & 
        (df_wb['Tanggal'].dt.month == sel_month_int)
    ].sort_values(by="Tanggal")

    # --- TABS (DITAMBAH TAB SETTING) ---
    tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard & Balance", "📝 Input Plan/Act", "📂 Database", "⚙️ Admin Settings"])

    # =========================================
    # TAB 1: DASHBOARD
    # =========================================
    with tab_dash:
        st.title(f"Laporan: {sel_month_name} {sel_year}")
        
        if df_wb_dash.empty:
            st.warning("⚠️ Data belum tersedia.")
        else:
            # A. METRICS
            last_row = df_wb_dash.iloc[-1]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Elevasi Terkini", f"{last_row['Elevasi Air (m)']} m", f"Limit: {last_row['Critical Elevation (m)']} m", delta_color="off")
            c2.metric("Volume Survey", f"{last_row['Volume Air Survey (m3)']:,.0f} m³")
            c3.metric("Hujan (Act)", f"{df_wb_dash['Curah Hujan (mm)'].sum():.1f} mm")
            status_clr = "#e74c3c" if last_row['Status'] == "BAHAYA" else "#27ae60"
            c4.markdown(f"<div style='background-color:{status_clr};color:white;padding:10px;border-radius:5px;text-align:center;'><b>{last_row['Status']}</b></div>", unsafe_allow_html=True)

            st.markdown("---")

            # B. GRAFIK SUMP UTAMA
            st.subheader("📈 Tren Hidrologi (Elevasi & Volume)")
            fig_sump = go.Figure()
            # Bar Volume
            fig_sump.add_trace(go.Bar(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], 
                name='Volume', marker_color='#AED6F1', opacity=0.6, yaxis='y2',
                text=df_wb_dash['Volume Air Survey (m3)'], texttemplate='%{text:.2s}', textposition='auto'
            ))
            # Line Critical
            fig_sump.add_trace(go.Scatter(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], 
                name='Critical Level', line=dict(color='red', dash='dash', width=2)
            ))
            # Line Actual Elevasi
            fig_sump.add_trace(go.Scatter(
                x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], 
                name='Elevasi Aktual', mode='lines+markers+text',
                line=dict(color='#21618C', width=3),
                text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
            ))
            fig_sump.update_layout(
                yaxis=dict(title="Elevasi (m)", side="left"),
                yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
                xaxis=dict(tickformat="%d", title="Tanggal"),
                legend=dict(orientation="h", y=1.1, x=0),
                height=400, margin=dict(t=30, b=20)
            )
            st.plotly_chart(fig_sump, use_container_width=True)

            st.markdown("---")
            
            # C. WATER BALANCE CHECKER
            st.subheader("⚖️ Water Balance Check")
            wb_today = last_row
            wb1, wb2, wb3, wb4, wb5 = st.columns(5)
            wb1.metric("1. Vol Kemarin", f"{wb_today['Volume Kemarin']:,.0f}")
            wb2.metric("2. Air Masuk", f"{wb_today['Volume In (Rain)']:,.0f}")
            wb3.metric("3. Air Keluar", f"{wb_today['Volume Out']:,.0f}")
            wb4.metric("4. Hitungan", f"{wb_today['Volume Teoritis']:,.0f}")
            wb5.metric("5. Survey (Act)", f"{wb_today['Volume Air Survey (m3)']:,.0f}")
            
            if pd.notna(wb_today['Error %']) and wb_today['Error %'] > 5.0:
                st.error(f"🚨 MISMATCH > 5%! Selisih: {wb_today['Error %']:.1f}% ({wb_today['Diff Volume']:,.0f} m³). Cek Seepage, Catchment, atau Pompa.")
            else:
                st.success(f"✅ Data Valid. Selisih: {wb_today['Error %']:.1f}%")

            # D. CURAH HUJAN & POMPA GRID
            st.markdown("---")
            c_left, c_right = st.columns([1, 2])
            
            with c_left:
                st.subheader("🌧️ Hujan (Plan Line vs Act Bar)")
                fig_rain = go.Figure()
                
                # 1. PLAN HUJAN (GARIS)
                fig_rain.add_trace(go.Scatter(
                    x=df_wb_dash['Tanggal'], 
                    y=df_wb_dash['Plan Curah Hujan (mm)'], 
                    name='Plan (Limit)', 
                    mode='lines',
                    line=dict(color='#e74c3c', width=2, dash='dash') 
                ))
                
                # 2. ACTUAL HUJAN (BAR)
                fig_rain.add_trace(go.Bar(
                    x=df_wb_dash['Tanggal'], 
                    y=df_wb_dash['Curah Hujan (mm)'], 
                    name='Actual (mm)', 
                    marker_color='#2c3e50',
                    opacity=0.8,
                    text=df_wb_dash['Curah Hujan (mm)'], 
                    textposition='outside'
                ))
                
                fig_rain.update_layout(
                    yaxis_title="Curah Hujan (mm)", 
                    legend=dict(orientation="h", y=1.1),
                    height=350, margin=dict(t=20, b=20)
                )
                st.plotly_chart(fig_rain, use_container_width=True)
                
            with c_right:
                st.subheader("⚙️ Detail Pompa")
                if not df_p_filt.empty:
                    sel_unit = st.selectbox("Unit:", df_p_filt['Unit Code'].unique())
                    df_u = df_p_filt[df_p_filt['Unit Code'] == sel_unit].sort_values(by="Tanggal")
                    
                    cp1, cp2 = st.columns(2)
                    with cp1:
                        st.caption("Debit (m3/h)")
                        fig_d = go.Figure()
                        fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Plan (m3/h)'], name='Plan', marker_color='#bdc3c7'))
                        fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Actual (m3/h)'], name='Actual', marker_color='#27ae60', text=df_u['Debit Actual (m3/h)'], textposition='auto'))
                        fig_d.update_layout(barmode='group', height=300, showlegend=False, margin=dict(t=0, b=0))
                        st.plotly_chart(fig_d, use_container_width=True)
                    with cp2:
                        st.caption("EWH (Jam)")
                        fig_e = go.Figure()
                        fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Plan'], name='Plan', marker_color='#bdc3c7'))
                        fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Actual'], name='Actual', marker_color='#e67e22', text=df_u['EWH Actual'], textposition='auto'))
                        fig_e.update_layout(barmode='group', height=300, showlegend=False, margin=dict(t=0, b=0))
                        st.plotly_chart(fig_e, use_container_width=True)

    # =========================================
    # TAB 2: INPUT
    # =========================================
    with tab_input:
        st.subheader("📝 Input Data")
        with st.container():
            c1, c2, c3 = st.columns(3)
            date_in = c1.date_input("Tanggal", date.today())
            
            # Dropdown dinamis dari site_map
            site_in = c2.selectbox("Site", list(st.session_state['site_map'].keys()), key="s_in")
            pit_in = c3.selectbox("Pit", st.session_state['site_map'][site_in], key="p_in")
        
        st.divider()
        cl, cr = st.columns(2)
        with cl:
            st.markdown("**1. Data Sump**")
            with st.form("f_sump"):
                c_s1, c_s2 = st.columns(2)
                e_act = c_s1.number_input("Elevasi (m)", format="%.2f")
                e_crit = c_s2.number_input("Critical (m)", value=13.0)
                vol = c_s1.number_input("Volume Survey (m3)", step=100)
                catch = c_s2.number_input("Catchment (Ha)", format="%.2f")
                c_r1, c_r2 = st.columns(2)
                rain_plan = c_r1.number_input("Hujan Plan (mm)", value=0.0)
                rain_act = c_r2.number_input("Hujan Actual (mm)", value=0.0)
                if st.form_submit_button("Simpan Sump"):
                    new_row = {
                        "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                        "Elevasi Air (m)": e_act, "Critical Elevation (m)": e_crit,
                        "Volume Air Survey (m3)": vol, "Plan Curah Hujan (mm)": rain_plan,
                        "Curah Hujan (mm)": rain_act, "Actual Catchment (Ha)": catch, 
                        "Status": "BAHAYA" if e_act > e_crit else "AMAN"
                    }
                    st.session_state.data_sump = pd.concat([pd.DataFrame([new_row]), st.session_state.data_sump], ignore_index=True)
                    st.success("Sump Tersimpan!")
        with cr:
            st.markdown("**2. Data Pompa**")
            with st.form("f_pump"):
                u_code = st.text_input("Unit Code (e.g. WP-01)")
                c_p1, c_p2 = st.columns(2)
                d_plan = c_p1.number_input("Debit Plan", value=500)
                d_act = c_p2.number_input("Debit Act", value=450)
                c_p3, c_p4 = st.columns(2)
                ewh_plan = c_p3.number_input("EWH Plan", value=20.0)
                ewh_act = c_p4.number_input("EWH Act", value=18.0)
                if st.form_submit_button("Simpan Pompa"):
                    new_p = {
                        "Tanggal": pd.to_datetime(date_in), "Site": site_in, "Pit": pit_in,
                        "Unit Code": u_code, "Debit Plan (m3/h)": d_plan,
                        "Debit Actual (m3/h)": d_act, "EWH Plan": ewh_plan, "EWH Actual": ewh_act
                    }
                    st.session_state.data_pompa = pd.concat([pd.DataFrame([new_p]), st.session_state.data_pompa], ignore_index=True)
                    st.success("Pompa Tersimpan!")

    # =========================================
    # TAB 3: DATABASE
    # =========================================
    with tab_db:
        st.subheader("📂 Download Center")
        dl_site = st.selectbox("Site Download:", list(st.session_state['site_map'].keys()))
        df_s_dl = st.session_state.data_sump[st.session_state.data_sump['Site'] == dl_site]
        df_p_dl = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == dl_site]
        
        if not df_s_dl.empty:
            df_join = pd.merge(df_s_dl, df_p_dl, on=['Tanggal', 'Site', 'Pit'], how='outer', suffixes=('_Sump', '_Pump'))
            st.dataframe(df_join.head(3), use_container_width=True)
            st.download_button("⬇️ Download CSV Gabungan", df_join.to_csv(index=False).encode('utf-8'), f"Report_{dl_site}.csv", "text/csv")
            
    # =========================================
    # TAB 4: ADMIN SETTINGS (BARU)
    # =========================================
    with tab_admin:
        st.subheader("⚙️ Manajemen Site & Pit")
        st.info("Di sini Anda bisa menambahkan Site baru atau Pit baru ke dalam sistem.")
        
        col_add1, col_add2 = st.columns(2)
        
        with col_add1:
            st.markdown("#### Tambah Site Baru")
            new_site_name = st.text_input("Nama Site Baru")
            if st.button("➕ Tambah Site"):
                if new_site_name and new_site_name not in st.session_state['site_map']:
                    st.session_state['site_map'][new_site_name] = []
                    st.success(f"Site '{new_site_name}' berhasil ditambahkan! Silakan refresh atau pindah tab.")
                    st.rerun()
                elif new_site_name in st.session_state['site_map']:
                    st.warning("Nama Site sudah ada.")
        
        with col_add2:
            st.markdown("#### Tambah Pit ke Site")
            target_site = st.selectbox("Pilih Site", list(st.session_state['site_map'].keys()))
            new_pit_name = st.text_input("Nama Pit Baru")
            if st.button("➕ Tambah Pit"):
                if new_pit_name and new_pit_name not in st.session_state['site_map'][target_site]:
                    st.session_state['site_map'][target_site].append(new_pit_name)
                    st.success(f"Pit '{new_pit_name}' berhasil ditambahkan ke {target_site}!")
                    st.rerun()
                else:
                    st.warning("Nama Pit kosong atau sudah ada.")
        
        st.divider()
        st.markdown("#### Daftar Site & Pit Saat Ini")
        st.json(st.session_state['site_map'])
