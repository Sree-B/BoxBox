import fastf1
import time

fastf1.Cache.enable_cache('cache')


def get_race_data(year, circuit_name, race_type):
    session = fastf1.get_session(year, circuit_name, race_type)
    session.load()          # <- this line MUST run successfully before the next line
    laps = session.laps     # <- this will fail if load() didn't complet
    cols = ['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'Position']   
    race_df = laps[cols].copy()
    race_df.to_csv(f'{circuit_name}_{year}.csv', index=False)
    return race_df

