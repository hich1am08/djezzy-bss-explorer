import pandas as pd

# Understand 2G naming
df2 = pd.read_excel('2G.xlsx', dtype=str)
sample = df2[df2['Cell Name'].str.contains('16X174', na=False)]
print('--- 2G for 16X174 ---')
for _, r in sample.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Freq. Band']}  BCCH={r.get('BCCH Frequency','-')}")
print()

# 3G naming
df3 = pd.read_excel('3G.xlsx', dtype=str)
sample3 = df3[df3['Cell Name'].str.contains('16X174', na=False)]
print('--- 3G for 16X174 ---')
for _, r in sample3.iterrows():
    print(f"  CellName={r['Cell Name']}  UARFCN={r['Downlink UARFCN']}")
print()

# 4G naming
df4 = pd.read_excel('4G.xlsx', dtype=str)
sample4 = df4[df4['Cell Name'].str.contains('16X174', na=False)]
print('--- 4G for 16X174 ---')
for _, r in sample4.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Frequency band']}  EARFCN={r['Downlink EARFCN']}")
print()

# 5G naming
df5 = pd.read_excel('5G.xlsx', dtype=str)
sample5 = df5[df5['Cell Name'].str.contains('16X174', na=False)]
print('--- 5G for 16X174 ---')
for _, r in sample5.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Frequency Band']}  NARFCN={r['Downlink NARFCN']}")

# Also check another site
print('\n\n=== ANOTHER SITE: 06X020 ===')
sample2g = df2[df2['Cell Name'].str.contains('06X020', na=False)]
print('--- 2G ---')
for _, r in sample2g.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Freq. Band']}")

sample3g = df3[df3['Cell Name'].str.contains('06X020', na=False)]
print('--- 3G ---')
for _, r in sample3g.iterrows():
    print(f"  CellName={r['Cell Name']}  UARFCN={r['Downlink UARFCN']}")

sample4g = df4[df4['Cell Name'].str.contains('06X020', na=False)]
print('--- 4G ---')
for _, r in sample4g.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Frequency band']}  EARFCN={r['Downlink EARFCN']}")

sample5g = df5[df5['Cell Name'].str.contains('06X020', na=False)]
print('--- 5G ---')
for _, r in sample5g.iterrows():
    print(f"  CellName={r['Cell Name']}  Band={r['Frequency Band']}")
