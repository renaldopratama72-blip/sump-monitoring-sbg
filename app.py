import streamlit as st
import pandas as pd
from datetime import date
import os

# Import Modules
# Pastikan file database.py, processing.py, dan ui.py ada di folder yang sama
import database as db
import processing as proc
import ui

# --- 1. CONFIG & SETUP ---
st.set_page_config(
    page_title="Bara Tama Wijaya Water Management",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)
ui.load_css()

# --- 2. SESSION STATE & DATA LOADING ---
if 'data_sump' not in st.session_state or 'data_pompa' not in st.session_state:
    try:
        df_s, df_p = db.load_data()
        st.session_state['data_sump'] = df_s
        st.session_state['data_pompa'] = df_p
    except Exception as e:
        st.error(f"Gagal koneksi ke Neon DB: {e}")
        st.stop()

if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if 'username' not in st.session_state: st.session_state['username'] = ''
if 'site_map' not in st.session_state:
    # Build dynamic site map from DB data
    if not st.session_state.data_sump.empty:
        existing_sites = st.session_state.data_sump['Site'].unique()
        current_map = {}
        for s in existing_sites:
            pits = st.session_state.data_sump[st.session_state.data_sump['Site'] == s]['Pit'].unique().tolist()
            current_map[s] = pits
        st.session_state['site_map'] = current_map
    else:
        st.session_state['site_map'] = {}

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown("## 🏢 BARA TAMA WIJAYA")
    if st.session_state['logged_in']:
        st.success(f"👤 Login: {st.session_state['username']}")
        if st.button("Logout", use_container_width=True):
            st.session_state['logged_in'] = False; st.rerun()
    else:
        st.info("👀 Mode: View Only")
    
    st.divider()
    
    # FILTERS
    current_sites = list(st.session_state['site_map'].keys())
    selected_site = st.selectbox("📍 Pilih Site", current_sites) if current_sites else None
    
    pit_options = ["All Sumps"]
    if selected_site and selected_site in st.session_state['site_map']: 
        pit_options += st.session_state['site_map'][selected_site]
    selected_pit = st.selectbox("💧 Pilih Sump", pit_options)

    # Unit Filter Logic
    unit_options = ["All Units"]
    if selected_pit != "All Sumps" and not st.session_state.data_pompa.empty:
        raw_p = st.session_state.data_pompa
        avail_units = raw_p[(raw_p['Site'] == selected_site) & (raw_p['Pit'] == selected_pit)]['Unit Code'].unique().tolist()
        unit_options += sorted(avail_units)
    selected_unit = st.selectbox("🚜 Pilih Unit Pompa", unit_options)
    
    # Date Filter
    avail_years = sorted(st.session_state.data_sump['Tanggal'].dt.year.unique(), reverse=True) if not st.session_state.data_sump.empty else [date.today().year]
    sel_year = st.selectbox("📅 Tahun", avail_years)
    month_map = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    curr_m = date.today().month
    sel_month_name = st.selectbox("🗓️ Bulan", list(month_map.values()), index=curr_m-1)
    sel_month_int = [k for k,v in month_map.items() if v==sel_month_name][0]

# --- 4. DATA PROCESSING ---
df_wb_dash, df_p_display, title_suffix = proc.process_water_balance(
    st.session_state.data_sump, st.session_state.data_pompa,
    selected_site, selected_pit, selected_unit, sel_year, sel_month_int
)

# --- 5. TABS ---
st.markdown(f"## 🏢 Bara Tama Wijaya: {selected_site}")
tab_dash, tab_input, tab_db, tab_admin = st.tabs(["📊 Dashboard", "📝 Input (Admin)", "📂 Database", "⚙️ Setting"])

# TAB 1: DASHBOARD
with tab_dash:
    if df_wb_dash.empty:
        st.warning("⚠️ Data belum tersedia untuk filter ini. Silakan generate dummy data di tab Setting atau input manual.")
    else:
        last = df_wb_dash.iloc[-1]
        
        # --- HEADER ---
        st.markdown(f"<div class='date-header'>📅 Dashboard Status per Tanggal: {last['Tanggal'].strftime('%d %B %Y')}</div>", unsafe_allow_html=True)
        
        # --- METRICS ---
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Elevasi Air", f"{last['Elevasi Air (m)']} m", f"Crit: {last['Critical Elevation (m)']}")
        c2.metric("Vol Survey", f"{last['Volume Air Survey (m3)']:,.0f} m³")
        
        # Rain metrics
        rain_today = last['Curah Hujan (mm)']
        rain_mtd = df_wb_dash['Curah Hujan (mm)'].sum()
        c3.metric("Rain Today", f"{rain_today} mm")
        c4.metric("Rain MTD", f"{rain_mtd} mm")
        
        # Status Box
        status_txt = "AMAN"; clr = "#27ae60"
        if last['Status'] == "BAHAYA": clr = "#e74c3c"; status_txt = "BAHAYA"
        c5.markdown(f"<div style='background-color:{clr};color:white;padding:20px;border-radius:5px;text-align:center;font-weight:bold;'>{status_txt}</div>", unsafe_allow_html=True)
        
        st.markdown("---")

        # --- WATER BALANCE WARNING BANNER ---
        last_error = last['Error %']
        is_wb_critical = False
        
        if last_error > 5.0 or pd.isna(last_error):
            is_wb_critical = True
            st.markdown(f"""
            <div class="wb-alert" style='background-color: #ffcccc; color: #cc0000; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; border: 1px solid #ff0000;'>
                ⚠️ PERINGATAN WATER BALANCE: Error {last_error:.1f}% (Melebihi Toleransi 5%)<br>
                Selisih Volume: {last['Diff Volume']:,.0f} m³
            </div>
            """, unsafe_allow_html=True)
            
        # --- CHARTS (From ui.py) ---
        ui.render_charts(df_wb_dash, df_p_display, title_suffix)

        # --- DETAIL TABLE ---
        with st.expander("📋 Lihat Detail Angka Water Balance"):
            df_show = df_wb_dash[['Tanggal', 'Volume Air Survey (m3)', 'Volume Teoritis', 'Diff Volume', 'Error %']].copy()
            df_show['Tanggal'] = df_show['Tanggal'].dt.strftime('%d-%m-%Y')
            
            st.dataframe(
                df_show.style.format({
                    'Volume Air Survey (m3)': '{:,.0f}',
                    'Volume Teoritis': '{:,.0f}', 
                    'Diff Volume': '{:,.0f}',
                    'Error %': '{:.1f}%'
                }), 
                hide_index=True, 
                use_container_width=True
            )

        # --- ANALYSIS & RECOMMENDATION BOXES ---
        st.markdown("---")
        st.subheader("🧠 Analisa & Rekomendasi")
        
        col_an, col_rec = st.columns(2)
        
        # Determine Status for Boxes
        if is_wb_critical:
            style_box = "danger-box"
            header_text = "🚨 PERINGATAN: DATA TIDAK BALANCE"
            bg_color = "#fdedec"
            border_color = "#e74c3c"
        elif last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
            style_box = "danger-box"
            header_text = "🚨 BAHAYA: ELEVASI TINGGI"
            bg_color = "#fdedec"
            border_color = "#e74c3c"
        else:
            style_box = "analysis-box"
            header_text = "✅ KONDISI AMAN"
            bg_color = "#e8f6f3"
            border_color = "#1abc9c"

        with col_an:
            st.markdown(f"""
            <div style='background-color: {bg_color}; padding: 15px; border-radius: 10px; border-left: 5px solid {border_color};'>
                <h4>{header_text}</h4>
                <ul>
                    <li><b>Status Water Balance:</b> Error {last_error:.1f}%.</li>
                    <li><b>Curah Hujan Hari Ini:</b> {rain_today} mm.</li>
                    <li><b>Status Elevasi:</b> {last['Elevasi Air (m)']} m.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        with col_rec:
            st.markdown(f"""
            <div style='background-color: #fef9e7; padding: 15px; border-radius: 10px; border-left: 5px solid #f1c40f;'>
                <h4>🛠️ REKOMENDASI</h4>
            """, unsafe_allow_html=True)
            
            rec_list = []
            
            if is_wb_critical:
                rec_list.append("🔴 <b>CEK INPUT DATA (HUMAN ERROR):</b> Pastikan angka Elevasi, Debit, dan Hujan yang diinput sudah benar.")
                rec_list.append("🔴 <b>Cek Groundwater:</b> Apakah ada air tanah/rembesan besar yang belum diinput di kolom Groundwater?")
                rec_list.append("🔴 <b>Cek Debit Pompa:</b> Verifikasi flowmeter pompa.")
            
            if last['Elevasi Air (m)'] >= last['Critical Elevation (m)']:
                rec_list.append("⛔ <b>STOP OPERASI & EVAKUASI UNIT.</b>")
            
            if not rec_list:
                st.markdown("- ✅ Data Valid & Operasi Aman.")
            else:
                for r in rec_list:
                    st.markdown(f"- {r}", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

# TAB 2: INPUT
with tab_input:
    if not st.session_state['logged_in']:
        ui.render_login_form("input")
    else:
        st.info("Input Data Harian (Saved to Neon Cloud)")
        with st.expander("➕ Input Harian Baru", expanded=True):
            d_in = st.date_input("Tanggal", date.today())
            
            # --- FIXED LOGIC FOR SUMP SELECTION ---
            existing_sumps = st.session_state['site_map'].get(selected_site, [])
            p_in = None 
            
            if not existing_sumps:
                st.warning(f"Belum ada Sump di {selected_site}. Silakan buat baru.")
                p_in = st.text_input("Nama Sump Baru (Wajib Diisi)", placeholder="Contoh: Sump Utara")
            else:
                mode_input = st.radio("Mode Input Sump:", ["Pilih Sump Ada", "Buat Sump Baru"], horizontal=True)
                if mode_input == "Pilih Sump Ada":
                    p_in = st.selectbox("Pilih Sump", existing_sumps)
                else:
                    p_in = st.text_input("Nama Sump Baru", placeholder="Contoh: Sump Selatan")

            # --- FORM INPUT ---
            if p_in:
                cl, cr = st.columns(2)
                
                # --- KOLOM KIRI: DATA SUMP ---
                with cl:
                    with st.form("fs"):
                        st.markdown(f"<b>Data Sump: {p_in}</b>", unsafe_allow_html=True)
                        e_a = st.number_input("Elevasi (m)", format="%.2f")
                        v_a = st.number_input("Volume Survey (m3)", step=100)
                        r_p = st.number_input("Rain Plan (mm)", value=20.0)
                        r_a = st.number_input("Rain Act (mm)", 0.0)
                        gw_v = st.number_input("Groundwater (m3)", 0.0)
                        
                        if st.form_submit_button("Simpan Sump"):
                            new = {
                                "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                                "Elevasi Air (m)": e_a, "Critical Elevation (m)": 13.0,
                                "Volume Air Survey (m3)": v_a, "Plan Curah Hujan (mm)": r_p,
                                "Curah Hujan (mm)": r_a, "Actual Catchment (Ha)": 25.0,
                                "Groundwater (m3)": gw_v,
                                "Status": "BAHAYA" if e_a > 13 else "AMAN"
                            }
                            db.save_new_sump(new)
                            
                            st.session_state['data_sump'], _ = db.load_data()
                            st.session_state.pop('site_map', None)
                            
                            st.success(f"Sump '{p_in}' Saved!")
                            st.rerun()

                # --- KOLOM KANAN: DATA POMPA (MODIFIED) ---
                with cr:
                    with st.form("fp"):
                        st.markdown(f"<b>Data Pompa: {p_in}</b>", unsafe_allow_html=True)
                        uc = st.text_input("Unit Code (e.g., WP-01)")
                        dp = st.number_input("Debit Plan (m3/h)", value=500)
                        da = st.number_input("Debit Actual (m3/h)", 0)
                        
                        ewh_p = st.number_input("EWH Plan (Jam)", value=20.0)
                        ea = st.number_input("EWH Actual (Jam)", 0.0)
                        
                        # --- STATUS & REMARKS ---
                        st.markdown("---")
                        st.caption("Status Operasi & Keterangan")
                        
                        opsi_status = [
                            "Running",
                            "Standby - Kandas (Air Habis)",
                            "Standby - Hujan/Licin",
                            "Standby - No Operator",
                            "Standby - General",
                            "Breakdown (BD) Unit",
                            "Breakdown (BD) Pipa",
                            "Schedule Maintenance"
                        ]
                        
                        # Auto-detect default status based on Hours
                        idx_def = 0 
                        if ea == 0: idx_def = 1 # Set to Standby if 0 hours
                        
                        status_ops = st.selectbox("Pilih Status Unit:", opsi_status, index=idx_def)
                        ket_rem = st.text_input("Remarks / Keterangan", placeholder="Contoh: Hose pecah, menunggu mekanik")
                        
                        if st.form_submit_button("Simpan Pompa"):
                            newp = {
                                "Tanggal": pd.to_datetime(d_in), "Site": selected_site, "Pit": p_in,
                                "Unit Code": uc, "Debit Plan (m3/h)": dp, "Debit Actual (m3/h)": da,
                                "EWH Plan": ewh_p, "EWH Actual": ea,
                                "Status Operasi": status_ops, # New Field
                                "Remarks": ket_rem            # New Field
                            }
                            db.save_new_pompa(newp)
                            _, st.session_state['data_pompa'] = db.load_data() # Reload
                            st.success(f"Pompa '{p_in}' Saved! (Status: {status_ops})")
                            st.rerun()
            else:
                if not existing_sumps:
                    st.info("Silakan ketik nama Sump baru di atas untuk memulai.")

        st.divider()
        st.markdown("### 🛠️ Bulk Edit (Delete Data here)")
        st.caption("Tips: Select rows and press 'Delete' on your keyboard to remove data. Click Update to save changes.")
        
        t1, t2 = st.tabs(["Edit Sump", "Edit Pompa"])
        with t1:
            curr_s = st.session_state.data_sump[st.session_state.data_sump['Site']==selected_site]
            ed_s = st.data_editor(curr_s, num_rows="dynamic", key="es")
            
            if st.button("💾 UPDATE SUMP DB"):
                full_s = pd.concat([st.session_state.data_sump[st.session_state.data_sump['Site']!=selected_site], ed_s], ignore_index=True)
                db.overwrite_full_db(full_s, st.session_state.data_pompa)
                st.session_state['data_sump'] = full_s
                st.session_state.pop('site_map', None)
                st.success("Updated!"); st.rerun()
                
        with t2:
            curr_p = st.session_state.data_pompa[st.session_state.data_pompa['Site']==selected_site]
            ed_p = st.data_editor(curr_p, num_rows="dynamic", key="ep")
            
            if st.button("💾 UPDATE POMPA DB"):
                full_p = pd.concat([st.session_state.data_pompa[st.session_state.data_pompa['Site']!=selected_site], ed_p], ignore_index=True)
                db.overwrite_full_db(st.session_state.data_sump, full_p)
                st.session_state['data_pompa'] = full_p
                st.success("Updated!"); st.rerun()

# TAB 3: DATABASE
with tab_db:
    st.info("📂 Source: Neon PostgreSQL")
    c1, c2 = st.columns(2)
    c1.download_button("Download Sump CSV", st.session_state.data_sump.to_csv(index=False), "sump.csv")
    c2.download_button("Download Pompa CSV", st.session_state.data_pompa.to_csv(index=False), "pompa.csv")
    st.dataframe(st.session_state.data_sump)

# TAB 4: ADMIN / SETTINGS
with tab_admin:
    st.markdown("### ⚙️ System Settings")
    
    if st.session_state['logged_in']:
        # Section 1: Manage Sites
        st.markdown("#### 🏗️ Manage Sites")
        ns = st.text_input("New Site Name")
        if st.button("Add Site") and ns: st.session_state['site_map'][ns] = []
        
        st.divider()
        
        # Section 2: Developer Tools
        st.markdown("#### 🧪 Developer Tools")
        
        c_dev1, c_dev2 = st.columns(2)
        
        with c_dev1:
            st.info("Gunakan ini untuk mengisi data grafik.")
            if st.button("Generate Dummy Data", type="primary", use_container_width=True):
                try:
                    with st.spinner("Generating data..."):
                        db.generate_dummy_data()
                        df_s, df_p = db.load_data()
                        st.session_state['data_sump'] = df_s
                        st.session_state['data_pompa'] = df_p
                        st.session_state.pop('site_map', None) 
                    st.success("Dummy data generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.error("Tip: Try 'Reset Database' below if this fails.")
                
        with c_dev2:
            st.info("Hapus hanya data dummy.")
            if st.button("Delete Dummy Data", type="secondary", use_container_width=True):
                with st.spinner("Cleaning up..."):
                    db.delete_dummy_data()
                    df_s, df_p = db.load_data()
                    st.session_state['data_sump'] = df_s
                    st.session_state['data_pompa'] = df_p
                    st.session_state.pop('site_map', None) 
                st.warning("Dummy data deleted.")
                st.rerun()

        st.divider()
        st.markdown("#### ⚠️ Danger Zone")
        
        # --- NEW DATABASE HELPER ---
        with st.expander("🛠️ Update Struktur Database (Wajib Klik Sekali)"):
            st.warning("Klik tombol ini JIKA Anda baru saja menambahkan kolom Status/Remarks dan belum update database.")
            if st.button("Tambah Kolom Status ke Tabel Pompa"):
                try:
                    if hasattr(db, 'conn'):
                        cur = db.conn.cursor()
                        cur.execute('ALTER TABLE pompa ADD COLUMN IF NOT EXISTS "Status Operasi" TEXT;')
                        cur.execute('ALTER TABLE pompa ADD COLUMN IF NOT EXISTS "Remarks" TEXT;')
                        db.conn.commit()
                        cur.close()
                        st.success("Sukses! Kolom Status & Remarks sudah ditambahkan.")
                    else:
                        st.error("Koneksi DB tidak ditemukan di modul database.")
                except Exception as e:
                    st.error(f"Gagal update DB: {e}")

        with st.expander("Reset Database (Fix Schema Errors)"):
            st.warning("This will DELETE ALL DATA (Real & Dummy) and recreate empty tables.")
            if st.button("🔴 RESET DATABASE (DROP TABLES)", type="primary"):
                with st.spinner("Resetting Database..."):
                    db.reset_db()
                    st.session_state.clear()
                st.success("Database has been reset. Please refresh the page.")
                
    else:
        ui.render_login_form("adm")
