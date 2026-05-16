"""
config.py
========================================
EASIEST PLACE TO ADD / REMOVE DAYS
Just edit the dictionaries below.
"""

import os

# =============================================
# CHANGE THIS PATH IF YOUR FOLDER IS DIFFERENT
# =============================================
DATA_FOLDER = r"C:\Users\divya\Desktop\Aerosol_layer"

# =============================================
# ADD / REMOVE DAYS HERE (very easy!)
# =============================================
day_files = {
    1: 'day_1.xlsx',
    2: 'day_2.xlsx',
    3: 'day_3.xlsx',
    4: 'day_4.xlsx',
   #5: 'day_5.xlsx',
   #6: 'day_6.xlsx',
    #7: 'day_7.xlsx',
    #8: 'day_8.xlsx',
    # 9: 'day_9.xlsx',      # ← Add new day like this
    # 10: 'day_10.xlsx',
}

stats_files = {
    1: 'stat_1.txt',
    2: 'stat_2.txt',
    3: 'stat_3.txt',
    4: 'stats.txt',
    5: 'stat_5.txt',
    6: 'stat_4.txt',
   # 7: 'stat_7.txt',
    #8: 'stat_8.txt',
    # 9: 'stat_9.txt',      # ← Add matching stats file
    # 10: 'stat_10.txt',
}