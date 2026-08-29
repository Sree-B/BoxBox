import streamlit as st
import pandas as pd
from data import get_race_data
from style import style_compound, style_delta, find_battles, get_track_status_label

st.set_page_config(layout="wide")
st.title("BoxBox")

@st.cache_data
def load_race_cached(year, circuit_name, race_type):
    return get_race_data(year, circuit_name, race_type)

col1, col2, col3 = st.columns(3)
year = col1.selectbox("Year", [2026])
circuit = col2.text_input("Circuit", "Barcelona")
race_type = col3.selectbox("Session", ["R"])

if st.button("Load Race") or 'race_data' in st.session_state:
    if 'race_data' not in st.session_state or st.session_state.get('race_key') != (year, circuit, race_type):
        race_data, results = load_race_cached(year, circuit, race_type)
        st.session_state.race_data = race_data
        st.session_state.results = results
        st.session_state.race_key = (year, circuit, race_type)
        st.session_state.lap = 1

    race_data = st.session_state.race_data
    results = st.session_state.results
    total_laps = int(race_data['LapNumber'].max())

    lap = st.slider("Lap", 1, total_laps, st.session_state.lap, key='lap')

    # build current from race_data -- this was the missing step
    current = race_data[race_data['LapNumber'] == lap].sort_values('Position').reset_index(drop=True)

    # track status banner
    lap_status = current['TrackStatus'].iloc[0] if not current.empty else None
    status_info = get_track_status_label(lap_status)
    if status_info:
        label, color = status_info
        st.markdown(
            f"<div style='background-color:{color}; color:black; padding:6px; "
            f"border-radius:4px; font-weight:bold; text-align:center;'>{label}</div>",
            unsafe_allow_html=True
        )

    # battles
    battles = find_battles(current, threshold=1.0)

    if battles:
        st.markdown("**⚔️ Battles**")
        battle_cols = st.columns(len(battles))
        for col, (ahead, behind, gap) in zip(battle_cols, battles):
            col.markdown(
                f"<div style='background-color:#2c2c2c; padding:8px; border-radius:6px; text-align:center;'>"
                f"⚔️ {ahead} vs {behind}<br><span style='color:#f39c12; font-weight:bold;'>{gap:.3f}s</span></div>",
                unsafe_allow_html=True
            )

    battling_drivers = set()
    for ahead, behind, _ in battles:
        battling_drivers.add(ahead)
        battling_drivers.add(behind)

    # build display table ONCE
    display = current[['Position', 'Driver', 'Compound', 'TyreLife', 'Interval', 'PersonalDelta', 'PittedThisLap']].copy()

    pit_icon = current['PittedThisLap'].apply(lambda x: ' 🔧' if x else '')
    battle_icon = current['Driver'].apply(lambda d: ' ⚔️' if d in battling_drivers else '')
    display['Driver'] = current['Driver'] + pit_icon + battle_icon
    display = display.drop(columns=['PittedThisLap'])
    display['TyreLife'] = display['TyreLife'].round(0).astype('Int64')

    st.caption("🔧 = pitted this lap · ⚔️ = in a close battle (gap < 1.0s)")

    styled = (display.style
        .applymap(style_compound, subset=['Compound'])
        .applymap(style_delta, subset=['PersonalDelta'])
        .format({'Interval': '{:.3f}', 'PersonalDelta': '{:+.3f}', 'TyreLife': '{:.0f}'}))

    st.dataframe(styled, use_container_width=True, hide_index=True)

    st.subheader("Race Status")
    not_running = results[results['Status'] != 'Finished']
    if not not_running.empty:
        st.dataframe(not_running[['Driver', 'Status']], hide_index=True)

    c1, c2 = st.columns(2)
    if c1.button("◀ Prev Lap") and lap > 1:
        st.session_state.lap = lap - 1
        st.rerun()
    if c2.button("Next Lap ▶") and lap < total_laps:
        st.session_state.lap = lap + 1
        st.rerun()
else:
    st.info("Select a race and click 'Load Race' to begin.")