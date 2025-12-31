import pandas as pd
import numpy as np

def process_water_balance(df_s, df_p, selected_site, selected_pit, selected_unit, year, month_int):
    """
    Filters data and calculates water balance logic.
    Returns: df_wb_dash (for dashboard), df_p_display (for pump charts), title_suffix
    """
    # 1. Filter Data by Site & Pit
    if selected_site and not df_s.empty:
        df_s = df_s[df_s['Site'] == selected_site]
        # Filter Pompa hanya jika datanya ada
        if not df_p.empty:
            df_p = df_p[df_p['Site'] == selected_site]

    if selected_pit != "All Sumps" and not df_s.empty:
        df_s = df_s[df_s['Pit'] == selected_pit]
        if not df_p.empty:
            df_p = df_p[df_p['Pit'] == selected_pit]

    # Initialize return variables
    df_wb_dash = pd.DataFrame()
    df_p_display = pd.DataFrame()
    title_suffix = ""

    if df_s.empty:
        return df_wb_dash, df_p_display, title_suffix

    # 2. Time Filter (Year & Month)
    # Filter Sump
    mask_s = (df_s['Tanggal'].dt.year == year) & (df_s['Tanggal'].dt.month == month_int)
    df_s_filt = df_s[mask_s].sort_values(by="Tanggal")
    
    # Filter Pompa
    if not df_p.empty:
        mask_p = (df_p['Tanggal'].dt.year == year) & (df_p['Tanggal'].dt.month == month_int)
        df_p_filt = df_p[mask_p].sort_values(by="Tanggal")
    else:
        df_p_filt = pd.DataFrame()

    # 3. Prepare Pump Display Data (For Charts)
    if not df_p_filt.empty:
        if selected_unit != "All Units":
            # Jika unit spesifik dipilih, kita ambil semua kolom (termasuk Status & Remarks)
            df_p_display = df_p_filt[df_p_filt['Unit Code'] == selected_unit].sort_values(by="Tanggal")
            title_suffix = f"Unit: {selected_unit}"
        else:
            # Jika All Units, kita rata-rata (Status & Remarks hilang karena tidak bisa dirata-rata)
            # Menggunakan numeric_only=True untuk menghindari error jika ada kolom text
            cols_to_avg = ['Debit Plan (m3/h)', 'Debit Actual (m3/h)', 'EWH Plan', 'EWH Actual']
            df_p_display = df_p_filt.groupby('Tanggal')[cols_to_avg].mean().reset_index()
            title_suffix = "Rata-rata Semua Unit"

    # 4. Water Balance Calculation
    if not df_s_filt.empty:
        # A. Hitung Volume Out (Total semua pompa di Pit tersebut)
        if not df_p_filt.empty:
            df_p_total = df_p_filt.copy()
            df_p_total['Volume Out'] = df_p_total['Debit Actual (m3/h)'] * df_p_total['EWH Actual']
            
            # Group by Tanggal, Site, Pit untuk mendapatkan total volume buang harian
            daily_out = df_p_total.groupby(['Site', 'Pit', 'Tanggal'])['Volume Out'].sum().reset_index()
            
            # Merge ke data Sump
            df_wb = pd.merge(df_s_filt, daily_out, on=['Site', 'Pit', 'Tanggal'], how='left')
            df_wb['Volume Out'] = df_wb['Volume Out'].fillna(0)
        else:
            df_wb = df_s_filt.copy()
            df_wb['Volume Out'] = 0

        # B. Inflow Logic
        # Asumsi: Actual Catchment x Curah Hujan x 10 = Volume Hujan (m3)
        df_wb['Volume In (Rain)'] = df_wb['Curah Hujan (mm)'] * df_wb['Actual Catchment (Ha)'] * 10
        df_wb['Volume In (GW)'] = df_wb['Groundwater (m3)'].fillna(0)

        # Sort agar perhitungan shift (kemarin) benar
        df_wb = df_wb.sort_values(by="Tanggal")
        
        # Ambil Volume Survey Hari Sebelumnya (Shift 1)
        df_wb['Volume Kemarin'] = df_wb['Volume Air Survey (m3)'].shift(1)

        # C. Balance Equation
        # Teoritis hari ini = Vol Kemarin + Hujan + Groundwater - Pompa
        df_wb['Volume Teoritis'] = df_wb['Volume Kemarin'] + df_wb['Volume In (Rain)'] + df_wb['Volume In (GW)'] - df_wb['Volume Out']
        
        # Diff = Survey Aktual - Teoritis
        df_wb['Diff Volume'] = df_wb['Volume Air Survey (m3)'] - df_wb['Volume Teoritis']
        
        # Error % (Handle division by zero)
        # Jika Volume Survey 0, set error ke 0 atau NaN agar tidak error
        df_wb['Error %'] = np.where(
            df_wb['Volume Air Survey (m3)'] > 0,
            (df_wb['Diff Volume'].abs() / df_wb['Volume Air Survey (m3)']) * 100,
            0.0
        )
        
        df_wb_dash = df_wb

    return df_wb_dash, df_p_display, title_suffix
