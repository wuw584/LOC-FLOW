import os
import pandas as pd
import datetime
import numpy as np

if __name__ == '__main__':
    result_dir = "results/pyocto"
    result_path = lambda x: os.path.join(result_dir, x)
    phaseSA_select = result_dir + "/phaseSA_select.txt"
    phaseSA_best_select = result_dir + "/phaseSA_best_select.txt"
    os.remove(phaseSA_select)
    os.remove(phaseSA_best_select)
    channle = []
    num = 0
    # pyocto_events = pd.read_csv(result_path("associate_cat.csv"), parse_dates=["time"])
    event_phase_sel = pd.read_csv(result_path("associate_list.csv"))
    for time, grp in event_phase_sel.groupby('time'):
        num += 1
        n_P_picks = len(grp.loc[grp['phase'] == 'P'].drop_duplicates())
        n_S_picks = len(grp.loc[grp['phase'] == 'S'].drop_duplicates())
        n_total_picks = len(grp)
        n_station = len(grp) - len(grp['station'].drop_duplicates())
        grp.loc[:, 'station'] = [int(i.split("-")[-1]) for i in grp['station']]
        x, y, z, picks, latitude, longitude, depth = grp.loc[
            grp.index[0], ['x', 'y', 'z', 'picks', 'latitude', 'longitude', 'depth']]
        grp["time_pick"] = grp["time_pick"].apply(datetime.datetime.fromtimestamp, tz=datetime.timezone.utc).__sub__(
            pd.to_datetime(time)).dt.total_seconds()
        with open(phaseSA_best_select, 'a') as f:
            g = grp
            g = g.loc[g['prob'] > 0.4]
            if len(g) > 0:
                f.write('# {}   {:.4f}   {:.4f}   {:.3f}  {:.2f}    {:.2f}    {:.2f}    {:.2f}      {} \n'.format(
                    pd.to_datetime(time).strftime('%Y %m %d %H %M %S.%f')[:-3], latitude, longitude, depth, 0, 0, 0, 0,
                    str(num).zfill(6)))
                for idx, row in g.sort_values(by='prob', ascending=False).head(40).iterrows():
                    f.write(
                        '{}   {:.4f} {:.4f} {}\n'.format(str(row['station']).zfill(5), row['time_pick'], row['prob'],
                                                         row['phase']))
                    channle.append(str(row['station']).zfill(5))
        with open(phaseSA_select, 'a') as f:
            g = grp
            f.write('# {}   {:.4f}   {:.4f}   {:.3f}  {:.2f}    {:.2f}    {:.2f}    {:.2f}      {} \n'.format(
                pd.to_datetime(time).strftime('%Y %m %d %H %M %S.%f')[:-3], latitude, longitude, depth, 0, 0, 0, 0,
                str(num).zfill(6)))
            arr = np.linspace(0, len(g) - 1, num=min(500, len(g)), dtype=int)
            for idx, row in g.sort_values(by='station').iterrows():
                if idx in g.index[arr]:
                    f.write('{}  {:.3f} 1 {}\n'.format(str(row['station']).zfill(5), row['time_pick'], row['phase']))
                    channle.append(str(row['station']).zfill(5))

    stations = pd.read_csv(result_path("statons.csv"), sep='\s+')
    stations['station_id'] = [str(int(i.split('-')[-1])).zfill(5) for i in stations['id']]
    stations = stations.loc[stations['station_id'].map(lambda x: x in channle)]
    stations['elevation_m'] = "1.00"
    stations['HHZ'] = 'DPZ'
    stations['net'] = 'XF'
    stations.to_csv((result_path("station.dat")),
                    columns=["longitude", "latitude", "net", "station_id", "HHZ", "elevation_m"], index=False,
                    header=False, sep=' ', float_format='%.6f')

    lat = 30
    lon = 121.7
    distmax = 100
    mode = 1

    station = result_path("station.dat")  # station direcotry
    vel = "./REAL/tt_db/mymodel.nd"  # velocity model directory
    phasein_best = result_path("phaseSA_best_select.txt")  # use the SA locations (for mode = 0 only)
    phasein = result_path("phaseSA_select.txt")  # use the relocated SA locations

    cur_dir = os.getcwd()
    os.chdir("./location/VELEST")
    command = f"perl convertformat.pl {lat} {lon} {distmax} {mode} {station} {vel} {phasein_best}"
    os.system(command)
    os.system("../../bin/velest")
    os.system(f"perl convertformat.pl {lat} {lon} {distmax} 1 {station} {vel} {phasein}")
    os.system("mv sta.COR velest.sta")
    os.system("mv velest.mod velest.mod.org")
    os.system("mv velout.mod velest.mod")
    os.system("velest_f.exe")

    # result format conversion and reselection
    stationgap = 300  # events with station gap larger than this will be discarded
    resmax = 0.5  # events with travel time residual larger than this will be discarded
    relocatalog = "new.cat"  # kept relocations
    deletedcatalog = "dele.cat"  # discarded relocations

    os.system(f"perl convertoutput.pl {stationgap} {resmax} {relocatalog} {deletedcatalog}")

    os.chdir(cur_dir)
    command = "cp ./location/VELEST/new.cat  " + result_path("velest.cat")
    print(command)
    os.system(command)
