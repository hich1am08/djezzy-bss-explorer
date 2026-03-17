import tracemalloc
import os
import pickle

cache_dir = '.cache'
data_store = {}

tracemalloc.start()

count = 0
for f in os.listdir(cache_dir):
    if f.endswith('.pkl'):
        path = os.path.join(cache_dir, f)
        with open(path, 'rb') as file:
            data_store[f] = pickle.load(file)
        count += 1

current, peak = tracemalloc.get_traced_memory()
print(f'Loaded {count} files.')
print(f'Current memory usage is {current / 10**6:.2f}MB; Peak was {peak / 10**6:.2f}MB')
tracemalloc.stop()
