import fastf1
import time

fastf1.Cache.enable_cache('cache')

session = fastf1.get_session(2026, 'Monaco', 'R')
session.load()          # <- this line MUST run successfully before the next line
time.sleep(0.5)
laps = session.laps     # <- this will fail if load() didn't complete
print(laps.columns)

ver_laps = laps.pick_driver('VER')
print('----------VERSTAPPEN----------')
print(ver_laps[['LapNumber', 'LapTime', 'Compound', 'TyreLife']])

ham_laps = laps.pick_driver('HAM')
print('----------HAMILTON----------')
print(ham_laps[['LapNumber', 'LapTime', 'Compound', 'TyreLife']])

ant_laps = laps.pick_driver('ANT')
print('----------ANTONELLI----------')
print(ant_laps[['LapNumber', 'LapTime', 'Compound', 'TyreLife']])

