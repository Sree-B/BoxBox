# style.py
import pandas as pd

COMPOUND_COLORS = {
    'SOFT': '#DA291C', 'MEDIUM': '#FFD12E', 'HARD': '#F0F0F0',
    'INTERMEDIATE': '#43B02A', 'WET': '#00A2FF'
}

def style_compound(val):
    color = COMPOUND_COLORS.get(val, '#888888')
    return f'background-color: {color}; color: black'

def style_delta(val):
    if pd.isna(val):
        return ''
    return 'color: #2ecc71' if val < 0 else 'color: #e74c3c'

def find_battles(lap_df, threshold=1.0):
    """lap_df must be sorted by Position. Returns list of (driver_ahead, driver_behind, gap)."""
    battles = []
    lap_df = lap_df.sort_values('Position').reset_index(drop=True)
    for i in range(1, len(lap_df)):
        gap = lap_df.loc[i, 'Interval']
        if pd.notna(gap) and gap < threshold:
            battles.append((
                lap_df.loc[i-1, 'Driver'],
                lap_df.loc[i, 'Driver'],
                gap
            ))
    return battles

def get_track_status_label(status_str):
    if pd.isna(status_str) or status_str == '1':
        return None  # green/clear, no banner needed
    if '5' in status_str:
        return ('RED FLAG', '#e74c3c')
    if '4' in status_str:
        return ('SAFETY CAR', '#f1c40f')
    if '6' in status_str:
        return ('VSC', '#f39c12')
    if '7' in status_str:
        return ('VSC ENDING', '#f39c12')
    if '2' in status_str:
        return ('YELLOW FLAG', '#f1c40f')
    return None