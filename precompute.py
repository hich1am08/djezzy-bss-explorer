import os
from app import create_app
from app.services.data_loader import load_all_data

app = create_app()
print("Starting pre-computation of datasets...")
with app.app_context():
    load_all_data()
print("Finished.")
