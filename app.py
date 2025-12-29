import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import numpy as np
import os

# --- 1. SETUP & CONFIG ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥", # Icon api/bara sesuai logo
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling Custom (CSS)
st.markdown("""
<style>
    .stApp { background-color: #f4f6f9; }
    div[data-testid="metric-container"] {
        background-color: #ffffff; border: 1px solid #e0e0e0;
        padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stAlert { font-weight: bold; }
    /* Mempercantik Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INITIALIZE SESSION STATE ---

# A. DATA LOGIN
USERS = {
    "englcm": "eng123",  # Admin LCM
    "engwsl": "eng123",  # Admin WSL
    "engne": "eng123",   # Admin NE
    "admin": "eng123"    # Super Admin
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = ''

# B. DYNAMIC SITE MAP (UPDATED NAMING: SUMP)
if 'site_map' not in st.session_state:
    st.session_state['site_map'] = {
        "Lais Coal Mine (LCM)": ["Sump Wijaya Barat", "Sump Wijaya Timur"],
        "Wiraduta Sejahtera Langgeng (WSL)": ["Sump F01", "Sump F02"],
        "Nusantara Energy (NE)": ["Sump S8"]
    }

# C. DATA GENERATOR
if 'data_sump' not in st.session_state:
    data = []
    today = date.today()
    current_map = st.session_state['site_map']
    
    for i in range(120):
        d = today - timedelta(days=i)
        for site in current_map.keys():
            if len(current_map[site]) > 0:
                pit = current_map[site][0] 
                rain_plan = np.random.choice([10, 20, 30, 40])
                rain_act = np.random.choice([0, 0, 0, 5, 15, 45, 60, 10])
                elev = 10.0 + (np.sin(i/15) * 3) + np.random.uniform(0, 0.5)
                vol = int(elev * 5000) 
                
                data.append({
                    "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                    "Elevasi Air (m)": round(elev, 2), "Critical Elevation (m)": 13.0,
                    "Volume Air Survey (m3)": vol,
                    "Plan Curah Hujan (mm)": rain_plan, "Curah Hujan (mm)": rain_act,         
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
                    data_p.append({
                        "Tanggal": pd.to_datetime(d), "Site": site, "Pit": pit,
                        "Unit Code": u, 
                        "Debit Plan (m3/h)": 500, "Debit Actual (m3/h)": np.random.randint(400, 480), 
                        "EWH Plan": 20.0, "EWH Actual": round(np.random.uniform(15, 22), 1)
                    })
    st.session_state.data_pompa = pd.DataFrame(data_p)

# Ensure types
st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])

# --- 3. SIDEBAR (LOGO & FILTER) ---
with st.sidebar:
    # --- LOGO AREA ---
    logo_file = "1.bara tama wijaya.jpg"
    if os.path.exists(logo_file):
        st.image(logo_file, use_container_width=True)
    else:
        # Fallback jika gambar belum diupload ke folder yang sama
        st.warning(f"File '{logo_file}' tidak ditemukan. Pastikan file ada di folder yang sama.")
        st.markdown("## BARA TAMA WIJAYA")
    
    st.markdown("<h3 style='text-align: center;'>Water Management</h3>", unsafe_allow_html=True)
    st.divider()
    
    # STATUS LOGIN
    if st.session_state['logged_in']:
        st.success(f"👤 Login: {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['username'] = ''
            st.rerun()
    else:
        st.info("👀 Mode: View Only")

    st.divider()

    # PILIH SITE
    current_sites = list(st.session_state['site_map'].keys())
    selected_site = st.selectbox("📍 Pilih Site", current_sites)
    
    pit_options = ["All Sumps"]
    if selected_site: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)
    
    st.caption("FILTER WAKTU")
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True)
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 4. CALCULATION ENGINE ---
df_s = st.session_state.data_sump.copy()
df_p = st.session_state.data_pompa.copy()

# Filter Wajib per Site
df_s = df_s[df_s['Site'] == selected_site]
df_p = df_p[df_p['Site'] == selected_site]

if selected_pit != "All Sumps":
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


# --- HELPER: LOGIN FORM FUNCTION ---
def render_login_form():
    with st.form("login_form"):
        st.subheader("🔒 Area Terbatas")
        st.write("Silakan login untuk mengakses halaman input ini.")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login Masuk")
        
        if submitted:
            if user in USERS and USERS[user] == pwd:
                st.session_state['logged_in'] = True
                st.session_state['username'] = user
                st.success("Login Berhasil! Loading...")
                st.rerun()
            else:
                st.error("Username atau Password Salah")

# --- 5. TABS ---
# Header Utama
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# =========================================
# TAB 1: DASHBOARD (PUBLIC)
# =========================================
with tab_dash:
    st.caption(f"Periode: {sel_month_name} {sel_year}")
    
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia untuk periode ini.")
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

        # B. GRAFIK SUMP
        st.subheader("📈 Tren Hidrologi Sump")
        fig_sump = go.Figure()
        # Warna Bar disesuaikan agak keunguan/abu agar tidak nabrak dengan logo orange
        fig_sump.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], 
            name='Volume', marker_color='#95a5a6', opacity=0.6, yaxis='y2',
            text=df_wb_dash['Volume Air Survey (m3)'], texttemplate='%{text:.2s}', textposition='auto'
        ))
        fig_sump.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], 
            name='Critical Level', line=dict(color='red', dash='dash', width=2)
        ))
        # Line utama diberi warna Orange sesuai identitas Bara Tama Wijaya
        fig_sump.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], 
            name='Elevasi Aktual', mode='lines+markers+text',
            line=dict(color='#e67e22', width=3),
            text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
        ))
        fig_sump.update_layout(
            yaxis=dict(title="Elevasi (m)", side="left"),
            yaxis2=dict(title="Volume (m3)", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", y=1.1), height=400, margin=dict(t=30, b=20)
        )
        st.plotly_chart(fig_sump, use_container_width=True)

        st.markdown("---")
        
        # C. WATER BALANCE
        st.subheader("⚖️ Water Balance Check")
        wb_today = last_row
        wb1, wb2, wb3, wb4, wb5 = st.columns(5)
        wb1.metric("1. Vol Kemarin", f"{wb_today['Volume Kemarin']:,.0f}")
        wb2.metric("2. Air Masuk", f"{wb_today['Volume In (Rain)']:,.0f}")
        wb3.metric("3. Air Keluar", f"{wb_today['Volume Out']:,.0f}")
        wb4.metric("4. Hitungan", f"{wb_today['Volume Teoritis']:,.0f}")
        wb5.metric("5. Survey (Act)", f"{wb_today['Volume Air Survey (m3)']:,.0f}")
        
        if pd.notna(wb_today['Error %']) and wb_today['Error %'] > 5.0:
            st.error(f"🚨 MISMATCH > 5%! Selisih: {wb_today['Error %']:.1f}% ({wb_today['Diff Volume']:,.0f} m³).")
        else:
            st.success(f"✅ Data Valid. Selisih: {wb_today['Error %']:.1f}%")

        # D. HUJAN & POMPA
        st.markdown("---")
        c_left, c_right = st.columns([1, 2])
        
        with c_left:
            st.subheader("🌧️ Curah Hujan")
            fig_rain = go.Figure()
            fig_rain.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'], name='Plan', mode='lines', line=dict(color='#e74c3c', width=2, dash='dash')))
            fig_rain.add_trace(go.Bar(x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'], name='Actual', marker_color='#2c3e50', opacity=0.8, text=df_wb_dash['Curah Hujan (mm)'], textposition='outside'))
            fig_rain.update_layout(yaxis_title="Curah Hujan (mm)", legend=dict(orientation="h", y=1.1), height=350, margin=dict(t=20, b=20))
            st.plotly_chart(fig_rain, use_container_width=True)
            
        with c_right:
            st.subheader("⚙️ Detail Pompa")
            if not df_p_filt.empty:
                sel_unit = st.selectbox("Unit:", df_p_filt['Unit Code'].unique())
                df_u = df_p_filt[df_p_filt['Unit Code'] == sel_unit].sort_values(by="Tanggal")
                cp1, cp2 = st.columns(2)
                with cp1:
                    fig_d = go.Figure()
                    fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Plan (m3/h)'], name='Plan', marker_color='#bdc3c7'))
                    fig_d.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['Debit Actual (m3/h)'], name='Actual', marker_color='#27ae60'))
                    fig_d.update_layout(title="Debit (m3/h)", barmode='group', height=300, showlegend=False, margin=dict(t=30, b=0))
                    st.plotly_chart(fig_d, use_container_width=True)
                with cp2:
                    fig_e = go.Figure()
                    fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Plan'], name='Plan', marker_color='#bdc3c7'))
                    fig_e.add_trace(go.Bar(x=df_u['Tanggal'], y=df_u['EWH Actual'], name='Actual', marker_color='#d35400')) # Orange Tua
                    fig_e.update_layout(title="EWH (Jam)", barmode='group', height=300, showlegend=False, margin=dict(t=30, b=0))
                    st.plotly_chart(fig_e, use_container_width=True)

# =========================================
# TAB 2: INPUT & EDIT (LOGIN REQUIRED)
# =========================================
with tab_input:
    if not st.session_state['logged_in']:
        render_login_form()
    else:
        st.subheader(f"📝 Kelola Data: {selected_site}")
        st.caption(f"Logged in as: {st.session_state['username']}")

        # --- BAGIAN 1: INPUT DATA BARU ---
        with st.expander("➕ Input Data Baru (Harian)", expanded=True):
            with st.container():
                c1, c2, c3 = st.columns(3)
                date_in = c1.date_input("Tanggal", date.today())
                st.info(f"Site: **{selected_site}**")
                site_in = selected_site 
                # Gunakan Label SUMP
                pit_in = c3.selectbox("Sump", st.session_state['site_map'][selected_site], key="p_in")
            
            cl, cr = st.columns(2)
            with cl:
                st.markdown("**Data Sump**")
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
                        st.success("Data Sump Tersimpan!")
            with cr:
                st.markdown("**Data Pompa**")
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
                        st.success("Data Pompa Tersimpan!")

        # --- BAGIAN 2: EDIT DATA LAMA (SEPERTI EXCEL) ---
        st.divider()
        st.subheader("✏️ Edit Data Lama (Excel Mode)")
        st.info("Klik langsung pada tabel di bawah untuk mengedit angka, lalu tekan tombol 'Simpan Perubahan'.")

        tab_edit_sump, tab_edit_pump = st.tabs(["Edit Sump", "Edit Pompa"])

        # EDIT SUMP
        with tab_edit_sump:
            df_current_site = st.session_state.data_sump[st.session_state.data_sump['Site'] == selected_site].sort_values(by="Tanggal", ascending=False)
            edited_sump = st.data_editor(
                df_current_site, 
                num_rows="dynamic", 
                hide_index=True,
                use_container_width=True,
                key="editor_sump"
            )
            if st.button("💾 Simpan Perubahan Sump"):
                st.session_state.data_sump = st.session_state.data_sump[st.session_state.data_sump['Site'] != selected_site]
                st.session_state.data_sump = pd.concat([st.session_state.data_sump, edited_sump], ignore_index=True)
                st.session_state.data_sump['Tanggal'] = pd.to_datetime(st.session_state.data_sump['Tanggal'])
                st.success("Data Sump Berhasil Di-update!")
                st.rerun()

        # EDIT POMPA
        with tab_edit_pump:
            df_current_pump = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == selected_site].sort_values(by="Tanggal", ascending=False)
            edited_pump = st.data_editor(
                df_current_pump, 
                num_rows="dynamic", 
                hide_index=True,
                use_container_width=True,
                key="editor_pump"
            )
            if st.button("💾 Simpan Perubahan Pompa"):
                st.session_state.data_pompa = st.session_state.data_pompa[st.session_state.data_pompa['Site'] != selected_site]
                st.session_state.data_pompa = pd.concat([st.session_state.data_pompa, edited_pump], ignore_index=True)
                st.session_state.data_pompa['Tanggal'] = pd.to_datetime(st.session_state.data_pompa['Tanggal'])
                st.success("Data Pompa Berhasil Di-update!")
                st.rerun()

# =========================================
# TAB 3: DATABASE (SEPARATE DOWNLOAD)
# =========================================
with tab_db:
    st.subheader("📂 Download Center")
    st.write(f"Menampilkan data untuk: **{selected_site}**")
    
    # Filter Data per Site
    df_s_dl = st.session_state.data_sump[st.session_state.data_sump['Site'] == selected_site]
    df_p_dl = st.session_state.data_pompa[st.session_state.data_pompa['Site'] == selected_site]
    
    col_dl1, col_dl2 = st.columns(2)

    # BAGIAN SUMP
    with col_dl1:
        st.markdown("### 💧 Data Sump")
        if not df_s_dl.empty:
            st.dataframe(df_s_dl.head(5), use_container_width=True)
            st.download_button(
                label="⬇️ Download CSV Sump", 
                data=df_s_dl.to_csv(index=False).encode('utf-8'), 
                file_name=f"Sump_{selected_site}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("Data Sump Kosong")

    # BAGIAN POMPA
    with col_dl2:
        st.markdown("### ⚙️ Data Pompa")
        if not df_p_dl.empty:
            st.dataframe(df_p_dl.head(5), use_container_width=True)
            st.download_button(
                label="⬇️ Download CSV Pompa", 
                data=df_p_dl.to_csv(index=False).encode('utf-8'), 
                file_name=f"Pompa_{selected_site}.csv", 
                mime="text/csv"
            )
        else:
            st.warning("Data Pompa Kosong")

# =========================================
# TAB 4: ADMIN SETTINGS (LOGIN REQUIRED)
# =========================================
with tab_admin:
    if not st.session_state['logged_in']:
        render_login_form()
    else:
        st.subheader("⚙️ Manajemen Site & Sump")
        
        col_add1, col_add2 = st.columns(2)
        with col_add1:
            st.markdown("#### Tambah Site Baru")
            new_site_name = st.text_input("Nama Site Baru")
            if st.button("➕ Tambah Site"):
                if new_site_name and new_site_name not in st.session_state['site_map']:
                    st.session_state['site_map'][new_site_name] = []
                    st.success(f"Site '{new_site_name}' ditambahkan!")
                    st.rerun()
        
        with col_add2:
            st.markdown("#### Tambah Sump ke Site")
            target_site = st.selectbox("Pilih Site yang mau diedit", list(st.session_state['site_map'].keys()))
            new_pit_name = st.text_input("Nama Sump Baru")
            if st.button("➕ Tambah Sump"):
                if new_pit_name and new_pit_name not in st.session_state['site_map'][target_site]:
                    st.session_state['site_map'][target_site].append(new_pit_name)
                    st.success(f"Sump '{new_pit_name}' ditambahkan ke {target_site}!")
                    st.rerun()
        
        st.divider()
        st.json(st.session_state['site_map'])
