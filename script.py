import pandas as pd
import sys
import os
import T1
import T2

if os.path.exists("Info.csv"):
    print("The data for task 1 has already been collected in the file Info.csv")
else:
    print("The data for task 1 still has to be collected. Expected time ~40 minutes")
    T1.retrieve_info()

if os.path.exists("FundingRounds.csv"):
    print("The data for task 2 has already been collected in the file FundingRounds.csv")
else:
    print("The data for task 2 still has to be collected. Expected time ~15 minutes")
    T2.exe()


