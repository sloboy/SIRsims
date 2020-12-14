
#### ERROR SOMETHING MISMATCH. WHY???  
#### Output files are empty. WHY? 

import numpy as np
import csv
import pandas as pd
import matplotlib.pyplot as plt

filenm = "Results/data_baseline_p0.txt"

text = np.loadtxt(filenm)
df = pd.DataFrame(text)
df.columns = [
    "l_asymp", 
    "l_sympt", 
    "i_asymp",
    "pre_sympt",
    "i_sympt",
    "home",
    "hospital",
    "icu",
    "recov",
    "new_l_asymp",
    "new_l_sympt",
    "new_i_asympt",
    "new_pre_sympt",
    "new_i_sympt",
    "new_home",
    "new_hostp",
    "new_icu",
    "new_recov",
    "run",]  # there are 100 runs

print(df)
by = df.groupby("run")

def plot_group(by, group):
    # Different groups have different lengths
    df = by.get_group(group)
    infected  = df["i_sympt"];
    pre_sympt = df["pre_sympt"]
    lat_sympt   = df["l_sympt"]
    recov     = df["recov"]
    total_recov = np.sum(recov)
    total_infected = np.sum(infected)
    total_pre_sympt = np.sum(pre_sympt)
    total_lat_sympt = np.sum(lat_sympt)
    print("totals l,p,i,r= ", 
        total_lat_sympt, total_pre_sympt, total_infected, total_recov)
    inf_s, = plt.plot(range(len(infected)),  infected,  color='r', label="infectious_s")
    pre_s, = plt.plot(range(len(pre_sympt)), pre_sympt, color='orange', label="pre_s")
    lat_s, = plt.plot(range(len(lat_sympt)),   lat_sympt,   color='b', label="latent_s")
    rec_,  = plt.plot(range(len(recov)), recov, color='g', label="recovered")
    handles = [inf_s, pre_s, lat_s, rec_]
    return handles

nb_runs = 5
for run in range(0, nb_runs):
    handles = plot_group(by, run)
plt.legend(handles=handles, loc='center right', ncol=1)
plt.show()
quit()

