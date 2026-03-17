import tracemalloc
import time

def test_loading():
    tracemalloc.start()
    print("Starting data_loader tests...")
    
    from app.services.data_loader import load_all_data, get_all_dataset_names, get_dataset_page
    
    load_all_data()
    
    names = get_all_dataset_names()
    print(f"Loaded {len(names)} dataset names.")
    
    if names:
        test_name = names[0]
        print(f"Testing lazy load of {test_name}...")
        records, total, cols = get_dataset_page(test_name)
        print(f"Page loaded: {len(records)} records out of {total} total. Columns: {len(cols)}")
        
    current, peak = tracemalloc.get_traced_memory()
    print(f"Memory Check: Current = {current / 10**6:.2f}MB, Peak = {peak / 10**6:.2f}MB")
    tracemalloc.stop()

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        test_loading()
