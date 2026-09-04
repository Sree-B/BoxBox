import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import get_race_data
from style import style_compound, style_delta, find_battles, get_track_status_label

st.set_page_config(layout="wide", page_title="BoxBox", page_icon="🏁")

# ---------------------------------------------------------------------------
# THEME / CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0e0e12; }
    #MainMenu, footer, header { visibility: hidden; }

    .bb-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 0;
        color: #f5f5f5;
    }
    .bb-subtitle {
        color: #8a8a94;
        font-size: 0.95rem;
        margin-top: -6px;
        margin-bottom: 1.2rem;
    }

    .bb-card {
        background: linear-gradient(145deg, #1a1a20, #17171c);
        border: 1px solid #262630;
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
    }
    .bb-card-label {
        color: #8a8a94;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .bb-card-value {
        color: #f5f5f5;
        font-size: 1.35rem;
        font-weight: 700;
    }
    .bb-card-sub {
        color: #f39c12;
        font-size: 0.78rem;
        margin-top: 2px;
    }

    .bb-flag-banner {
        padding: 10px;
        border-radius: 8px;
        font-weight: 700;
        text-align: center;
        margin-bottom: 14px;
        letter-spacing: 0.5px;
    }

    .bb-battle-card {
        background-color: #1c1c22;
        border: 1px solid #2c2c36;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
    }
    .bb-battle-gap {
        color: #f39c12;
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="bb-title">🏁 BoxBox</p>', unsafe_allow_html=True)
st.markdown('<p class="bb-subtitle">Lap-by-lap F1 race replay & strategy dashboard</p>', unsafe_allow_html=True)


@st.cache_data
def load_race_cached(year, circuit_name, race_type):
    return get_race_data(year, circuit_name, race_type)


def compute_stints(race_data, up_to_lap):
    """Build per-driver tire stints (compound + lap range) up to the current lap."""
    df = race_data[race_data['LapNumber'] <= up_to_lap].sort_values(['Driver', 'LapNumber'])
    rows = []
    for driver, grp in df.groupby('Driver'):
        grp = grp.reset_index(drop=True)
        start_lap = grp.loc[0, 'LapNumber']
        current_compound = grp.loc[0, 'Compound']
        for i in range(1, len(grp)):
            if grp.loc[i, 'Compound'] != current_compound:
                rows.append({
                    'Driver': driver, 'Compound': current_compound,
                    'Start': start_lap, 'End': grp.loc[i - 1, 'LapNumber']
                })
                start_lap = grp.loc[i, 'LapNumber']
                current_compound = grp.loc[i, 'Compound']
        rows.append({
            'Driver': driver, 'Compound': current_compound,
            'Start': start_lap, 'End': grp.loc[len(grp) - 1, 'LapNumber']
        })
    return pd.DataFrame(rows)


COMPOUND_COLORS = {
    'SOFT': '#e63946', 'MEDIUM': '#f4d35e', 'HARD': '#f5f5f5',
    'INTERMEDIATE': '#2a9d8f', 'WET': '#4361ee'
}


# ---------------------------------------------------------------------------
# SIDEBAR CONTROLS
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Race Setup")
    year = st.selectbox("Year", [2026])
    circuit = st.text_input("Circuit", "Barcelona")
    race_type = st.selectbox("Session", ["R"])
    load_clicked = st.button("Load Race", use_container_width=True)

if load_clicked or 'race_data' in st.session_state:
    if 'race_data' not in st.session_state or st.session_state.get('race_key') != (year, circuit, race_type):
        race_data, results = load_race_cached(year, circuit, race_type)
        st.session_state.race_data = race_data
        st.session_state.results = results
        st.session_state.race_key = (year, circuit, race_type)
        st.session_state.lap = 1

    race_data = st.session_state.race_data
    results = st.session_state.results
    total_laps = int(race_data['LapNumber'].max())

    with st.sidebar:
        st.divider()
        lap = st.slider("Lap", 1, total_laps, st.session_state.lap, key='lap')
        c1, c2 = st.columns(2)
        if c1.button("◀ Prev", use_container_width=True) and lap > 1:
            st.session_state.lap = lap - 1
            st.rerun()
        if c2.button("Next ▶", use_container_width=True) and lap < total_laps:
            st.session_state.lap = lap + 1
            st.rerun()

    current = race_data[race_data['LapNumber'] == lap].sort_values('Position').reset_index(drop=True)

    # track status
    lap_status = current['TrackStatus'].iloc[0] if not current.empty else None
    status_info = get_track_status_label(lap_status)
    if status_info:
        label, color = status_info
        st.markdown(
            f"<div class='bb-flag-banner' style='background-color:{color}; color:black;'>{label}</div>",
            unsafe_allow_html=True
        )

    # ---------------------------------------------------------------------
    # KPI HEADER ROW
    # ---------------------------------------------------------------------
    leader_row = current.iloc[0] if not current.empty else None
    fastest_lap_row = race_data.loc[race_data['LapSeconds'].idxmin()] if 'LapSeconds' in race_data.columns else None
    dnf_count = int((results['Status'] != 'Finished').sum())

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(f"""<div class="bb-card">
            <div class="bb-card-label">Lap</div>
            <div class="bb-card-value">{lap} / {total_laps}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="bb-card">
            <div class="bb-card-label">Leader</div>
            <div class="bb-card-value">{leader_row['Driver'] if leader_row is not None else '–'}</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        gap = current['Interval'].iloc[1] if len(current) > 1 else None
        st.markdown(f"""<div class="bb-card">
            <div class="bb-card-label">Gap 1st → 2nd</div>
            <div class="bb-card-value">{f'{gap:.3f}s' if gap is not None else '–'}</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        if fastest_lap_row is not None:
            fl_val = f"{fastest_lap_row['LapSeconds']:.3f}s"
            fl_sub = f"{fastest_lap_row['Driver']} · Lap {int(fastest_lap_row['LapNumber'])}"
        else:
            fl_val, fl_sub = "–", ""
        st.markdown(f"""<div class="bb-card">
            <div class="bb-card-label">Fastest Lap</div>
            <div class="bb-card-value">{fl_val}</div>
            <div class="bb-card-sub">{fl_sub}</div>
        </div>""", unsafe_allow_html=True)
    with k5:
        st.markdown(f"""<div class="bb-card">
            <div class="bb-card-label">Retirements</div>
            <div class="bb-card-value">{dnf_count}</div>
        </div>""", unsafe_allow_html=True)

    st.write("")

    # ---------------------------------------------------------------------
    # BATTLES — hidden during flags, limited to top 10 for first 2 laps
    # ---------------------------------------------------------------------
    battles = []
    if not status_info:
        battle_pool = current[current['Position'] <= 10] if lap <= 2 else current
        battles = find_battles(battle_pool, threshold=1.0)

    battling_drivers = set()
    for ahead, behind, _ in battles:
        battling_drivers.add(ahead)
        battling_drivers.add(behind)

    if battles:
        st.markdown("**⚔️ Battles**")
        battle_cols = st.columns(len(battles))
        for col, (ahead, behind, gap) in zip(battle_cols, battles):
            col.markdown(
                f"<div class='bb-battle-card'>⚔️ {ahead} vs {behind}<br>"
                f"<span class='bb-battle-gap'>{gap:.3f}s</span></div>",
                unsafe_allow_html=True
            )
        st.write("")

    # ---------------------------------------------------------------------
    # TABS: Timing | Tire Strategy | Gap Trend
    # ---------------------------------------------------------------------
    tab_timing, tab_tires, tab_gap = st.tabs(["📋 Live Timing", "🛞 Tire Strategy", "📈 Gap Trend"])

    with tab_timing:
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

        st.dataframe(styled, use_container_width=True, hide_index=True, height=560)

        st.subheader("Race Status")
        not_running = results[results['Status'] != 'Finished']
        if not not_running.empty:
            st.dataframe(not_running[['Driver', 'Status']], hide_index=True)
        else:
            st.caption("All cars currently classified as running.")

    with tab_tires:
        stints = compute_stints(race_data, lap)
        driver_order = current['Driver'].tolist() if not current.empty else stints['Driver'].unique().tolist()

        fig = go.Figure()
        for _, row in stints.iterrows():
            fig.add_trace(go.Bar(
                x=[row['End'] - row['Start'] + 1],
                y=[row['Driver']],
                base=[row['Start'] - 1],
                orientation='h',
                marker_color=COMPOUND_COLORS.get(row['Compound'], '#888'),
                name=row['Compound'],
                showlegend=False,
                hovertemplate=f"{row['Driver']}<br>{row['Compound']}<br>Laps {row['Start']}–{row['End']}<extra></extra>"
            ))

        fig.update_layout(
            barmode='stack',
            template='plotly_dark',
            plot_bgcolor='#0e0e12',
            paper_bgcolor='#0e0e12',
            height=650,
            xaxis_title="Lap",
            yaxis=dict(categoryorder='array', categoryarray=list(reversed(driver_order))),
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        legend_html = " &nbsp;&nbsp; ".join(
            f"<span style='color:{c}'>●</span> {name}" for name, c in COMPOUND_COLORS.items()
        )
        st.markdown(legend_html, unsafe_allow_html=True)

    with tab_gap:
        top5 = current['Driver'].head(5).tolist() if not current.empty else []
        hist = race_data[(race_data['LapNumber'] <= lap) & (race_data['Driver'].isin(top5))]

        fig2 = go.Figure()
        for driver in top5:
            d = hist[hist['Driver'] == driver].sort_values('LapNumber')
            fig2.add_trace(go.Scatter(
                x=d['LapNumber'], y=d['Interval'],
                mode='lines+markers', name=driver
            ))

        fig2.update_layout(
            template='plotly_dark',
            plot_bgcolor='#0e0e12',
            paper_bgcolor='#0e0e12',
            height=500,
            xaxis_title="Lap",
            yaxis_title="Gap to car ahead (s)",
            legend_title_text="Driver",
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("Interval to the car directly ahead, current top 5, through the selected lap.")

else:
    st.info("Set up a race in the sidebar and click **Load Race** to begin.")