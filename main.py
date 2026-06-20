import streamlit as st
import pandas as pd
from data import get_race_data

st.title("BoxBox")

# --- Race picker (loads into session_state so it survives reruns) ---
year = st.number_input("Year", min_value=2026, max_value=2026, value=2026)
circuit_name = st.text_input("Circuit", value="Monaco")

if st.button("Load Race"):
    st.session_state.race_df = get_race_data(year, circuit_name, 'R')

# --- Everything below only runs once a race is actually loaded ---
if 'race_df' in st.session_state:
    df = st.session_state.race_df
    lap = 20  # hardcoded for now — Task 6 makes this interactive
    snapshot = df[df['LapNumber'] == lap].sort_values('Position')

    st.caption(f"{circuit_name} {year} — Lap {lap}")
    st.divider()

    # Header row
    header = st.columns([1, 2, 2, 3, 2])
    header[0].markdown("**Pos**")
    header[1].markdown("**Driver**")
    header[2].markdown("**Tire**")
    header[3].markdown("**Wear**")
    header[4].markdown("**Tire Age**")

    compound_colors = {
        "SOFT": "#e10600",
        "MEDIUM": "#ffd700",
        "HARD": "#f0f0f0",
        "INTERMEDIATE": "#3cb371",
        "WET": "#1e90ff"
    }

    # Data rows
    for _, row in snapshot.iterrows():
        cols = st.columns([1, 2, 2, 3, 2])
        cols[0].write(f"P{int(row['Position'])}")
        cols[1].write(row['Driver'])

        color = compound_colors.get(row['Compound'], "#888888")
        cols[2].markdown(
            f"<span style='background-color:{color}; color:black; padding:2px 8px; "
            f"border-radius:4px; font-weight:bold;'>{row['Compound']}</span>",
            unsafe_allow_html=True
        )

        wear = min(row['TyreLife'] / 30, 1.0)
        cols[3].progress(wear)
        cols[4].write(f"{int(row['TyreLife'])} laps")
else:
    st.info("Pick a year and circuit, then click Load Race.")