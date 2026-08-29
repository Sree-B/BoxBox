import fastf1
import pandas as pd
import os

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

def load_session(year, circuit_name, race_type):
    session = fastf1.get_session(year, circuit_name, race_type)
    session.load()
    
    return session

def load_lap_data(session):
    laps = session.laps
    laps['PittedThisLap'] = laps['PitInTime'].notna()
    cols = ['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'Position', 'Time', 'PitInTime', 'PittedThisLap']
    
    return laps[cols].copy()

def load_race_results(session):

    results = session.results[['Abbreviation', 'Position', 'Status']].copy()
    return results.rename(columns={'Abbreviation': 'Driver'})

def add_personal_delta(race_data):
    race_data = race_data.copy()
    race_data['LapSeconds'] = race_data['LapTime'].dt.total_seconds()
    race_data = race_data.sort_values(['Driver', 'LapNumber'])
    race_data['PersonalDelta'] = race_data.groupby('Driver')['LapSeconds'].diff()
    return race_data

def add_interval(race_data):
    race_data = race_data.copy()
    race_data['CumSeconds'] = race_data['Time'].dt.total_seconds()

    records = []
    for lap_num, lap_group in race_data.groupby('LapNumber'):
        lap_group = lap_group.sort_values('Position')
        cum_times = lap_group['CumSeconds'].tolist()
        drivers = lap_group['Driver'].tolist()
        for i, driver in enumerate(drivers):
            gap = 0.0 if i == 0 else cum_times[i] - cum_times[i - 1]
            records.append({'Driver': driver, 'LapNumber': lap_num, 'Interval': gap})

    interval_race_data = pd.DataFrame(records)
    return race_data.merge(interval_race_data, on=['Driver', 'LapNumber'])


def get_race_data(year, circuit_name, race_type):
    session = load_session(year, circuit_name, race_type)
    session.load()

    race_data = load_lap_data(session)
    race_data = add_personal_delta(race_data)
    race_data = add_interval(race_data)
    race_data.to_csv(f'{circuit_name}_{year}_laps.csv', index=False)

    results = load_race_results(session)
    results.to_csv(f'{circuit_name}_{year}_results.csv', index=False)
    return race_data, results

if __name__ == "__main__":
    race_data, results = get_race_data(2026, 'Barcelona', 'R')

    check = race_data[race_data['LapNumber'] == 10].sort_values('Position')
    print(check[['Position', 'Driver', 'PersonalDelta', 'Interval', 'PittedThisLap']])

    print(results)

def load_lap_data(session):
    laps = session.laps
    laps['PittedThisLap'] = laps['PitInTime'].notna()
    cols = ['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'Position',
            'Time', 'PitInTime', 'PittedThisLap', 'TrackStatus']
    
    return laps[cols].copy()