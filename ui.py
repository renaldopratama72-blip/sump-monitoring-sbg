import streamlit as st
import plotly.graph_objects as go
import os

USERS = {"englcm": "eng123", "engwsl": "eng123", "engne": "eng123", "admin": "eng123"}

def load_css():
    st.markdown("""
    <style>
        /* =========================================
           MAIN CONTENT AREA FIXES
           ========================================= */
        
        /* 1. Force Main Background to Light Grey */
        .stApp {
            background-color: #f4f6f9 !important;
        }

        /* 2. FIX HEADERS (e.g., "Bara Tama Wijaya", "Analisa & Rekomendasi", "Tren Elevasi") */
        .main h1, .main h2, .main h3, .main h4, .main h5, .main h6 {
            color: #000000 !important;
        }

        /* 3. FIX METRICS (e.g., "Elevasi Air", "10.0 m", "Vol Survey") */
        /* The Label (Top small text) */
        [data-testid="stMetricLabel"] {
            color: #444444 !important; /* Dark Grey */
        }
        /* The Value (Big number) */
        [data-testid="stMetricValue"] {
            color: #000000 !important; /* Pure Black */
        }
        /* The Caption/Delta (e.g., "Crit: 13.0") */
        [data-testid="stMetricDelta"] > div {
            color: #333333 !important; /* Dark Grey (overrides default light grey) */
        }
        /* Ensure Metric Box Background is White */
        div[data-testid="metric-container"] {
            background-color: #ffffff !important;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }

        /* 4. FIX EXPANDERS (e.g., "📋 Lihat Detail Angka Water Balance") */
        .streamlit-expanderHeader {
            background-color: #ffffff !important;
            color: #000000 !important;
        }
        .streamlit-expanderHeader p {
            color: #000000 !important;
        }

        /* 5. FIX CUSTOM BOXES (e.g., "PERINGATAN", "REKOMENDASI") */
        /* Forces the container text to black */
        .analysis-box, .rec-box, .danger-box, .wb-alert {
            color: #000000 !important;
        }
        /* Forces the Headers inside boxes (e.g., <h4>REKOMENDASI</h4>) to black */
        .analysis-box h4, .rec-box h4, .danger-box h4, .wb-alert h4 {
            color: #000000 !important;
        }
        /* Forces List items (e.g., "🔴 Cek Input...") to black */
        .analysis-box li, .rec-box li, .danger-box li, .wb-alert li {
            color: #000000 !important;
        }
        /* Forces Bold text (e.g., <b>Status Water Balance:</b>) to black */
        .analysis-box b, .rec-box b, .danger-box b, .wb-alert b {
            color: #000000 !important;
        }
        /* Forces standard paragraphs inside boxes to black */
        .analysis-box p, .rec-box p, .danger-box p, .wb-alert p {
            color: #000000 !important;
        }

        /* 6. FIX GENERAL MARKDOWN TEXT (Fallback for other text) */
        .main p {
            color: #000000 !important;
        }

    </style>
    """, unsafe_allow_html=True)

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

def render_charts(df_wb_dash, df_p_display, title_suffix):
    # FORCE PLOTLY TO USE BLACK TEXT & TRANSPARENT BACKGROUND
    layout_settings = dict(
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="black") # Forces chart text to be black
    )

    # --- 1. WATER BALANCE & RAINFALL ---
    st.subheader("⚖️ Water Balance & Rainfall Analysis")
    col_wb1, col_wb2 = st.columns(2)
    
    with col_wb1:
        fig_rain = go.Figure()
        fig_rain.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Curah Hujan (mm)'], 
            name='Act Rain (mm)', marker_color='#3498db',
            text=df_wb_dash['Curah Hujan (mm)'], textposition='auto'
        ))
        fig_rain.add_trace(go.Scatter(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Plan Curah Hujan (mm)'], 
            name='Plan Rain (mm)', mode='lines+markers', line=dict(color='#e74c3c', dash='dot')
        ))
        fig_rain.update_layout(title="Rainfall: Plan vs Actual (mm)", height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1), **layout_settings)
        st.plotly_chart(fig_rain, use_container_width=True)

    with col_wb2:
        fig_wb = go.Figure()
        fig_wb.add_trace(go.Bar(x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (Rain)'], name='In (Rain)', marker_color='#3498db'))
        fig_wb.add_trace(go.Bar(x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume In (GW)'], name='In (Groundwater)', marker_color='#9b59b6'))
        fig_wb.add_trace(go.Bar(
            x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Out'], 
            name='Out (Total All Pumps)', marker_color='#e74c3c',
            text=df_wb_dash['Volume Out'], texttemplate='%{text:.0f}', textposition='auto'
        ))
        fig_wb.update_layout(title="Volume Flow (m³): In vs Out", barmode='group', height=350, margin=dict(t=30), legend=dict(orientation='h', y=1.1), **layout_settings)
        st.plotly_chart(fig_wb, use_container_width=True)

    # --- 2. ELEVATION ---
    st.markdown("---")
    st.subheader("🌊 Tren Elevasi Sump")
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(x=df_wb_dash['Tanggal'], y=df_wb_dash['Volume Air Survey (m3)'], name='Vol', marker_color='#95a5a6', opacity=0.3, yaxis='y2'))
    fig_s.add_trace(go.Scatter(
        x=df_wb_dash['Tanggal'], y=df_wb_dash['Elevasi Air (m)'], name='Elevasi', 
        mode='lines+markers+text', line=dict(color='#e67e22', width=3),
        text=df_wb_dash['Elevasi Air (m)'], texttemplate='%{text:.2f}', textposition='top center'
    ))
    fig_s.add_trace(go.Scatter(x=df_wb_dash['Tanggal'], y=df_wb_dash['Critical Elevation (m)'], name='Limit', line=dict(color='red', dash='dash')))
    fig_s.update_layout(
        yaxis2=dict(overlaying='y', side='right', showgrid=False, title="Volume (m3)"),
        yaxis=dict(title="Elevasi (m)"), legend=dict(orientation='h', y=1.1), height=400, margin=dict(t=30),
        **layout_settings
    )
    st.plotly_chart(fig_s, use_container_width=True)

    # --- 3. PUMP PERFORMANCE ---
    st.markdown("---")
    st.subheader(f"⚙️ Performa Pompa ({title_suffix})")
    if not df_p_display.empty:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            fig_d = go.Figure()
            fig_d.add_trace(go.Bar(x=df_p_display['Tanggal'], y=df_p_display['Debit Actual (m3/h)'], name='Act', marker_color='#2ecc71', text=df_p_display['Debit Actual (m3/h)'], texttemplate='%{text:.0f}', textposition='auto'))
            fig_d.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['Debit Plan (m3/h)'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_d.update_layout(title="Debit (m3/h)", legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=30), **layout_settings)
            st.plotly_chart(fig_d, use_container_width=True)
        with col_p2:
            fig_e = go.Figure()
            fig_e.add_trace(go.Bar(x=df_p_display['Tanggal'], y=df_p_display['EWH Actual'], name='Act', marker_color='#d35400', text=df_p_display['EWH Actual'], texttemplate='%{text:.1f}', textposition='auto'))
            fig_e.add_trace(go.Scatter(x=df_p_display['Tanggal'], y=df_p_display['EWH Plan'], name='Plan', line=dict(color='#2c3e50', dash='dash')))
            fig_e.update_layout(title="EWH (Jam)", legend=dict(orientation='h', y=1.1), height=300, margin=dict(t=30), **layout_settings)
            st.plotly_chart(fig_e, use_container_width=True)
    else:
        st.info("Data Pompa tidak ditemukan untuk filter ini.")