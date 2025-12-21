import pandas as pd
import numpy as np
from datetime import datetime

def clean_csv_data(input_file: str, output_file: str):
    # Read the raw CSV, skipping metadata rows
    df = pd.read_csv(input_file, skiprows=10, header=0)
    
    # Extract metadata
    location = "Newcastle Centre"
    latitude = 54.97825
    longitude = -1.610528
    site_type = "Urban Background"
    zone = "North East"
    
    # Clean column names
    df.columns = [col.strip() for col in df.columns]
    
    # Convert date column
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')
    
    # Define pollutant columns (value columns only)
    pollutant_cols = {
        'Black Carbon (880nm)': 'black_carbon_880nm',
        'Infra Red Particulate matter (950nm)': 'infrared_pm_950nm',
        'Red Particulate matter (660nm)': 'red_pm_660nm',
        'Yellow Particulate matter (590nm)': 'yellow_pm_590nm',
        'Green Particulate matter (520nm)': 'green_pm_520nm',
        'Blue Particulate matter (470nm)': 'blue_pm_470nm',
        'UV Particulate Matter (370nm)': 'uv_pm_370nm'
    }
    
    # Create clean dataset
    clean_data = []
    
    for _, row in df.iterrows():
        if pd.isna(row['Date']):
            continue
            
        for original_col, clean_col in pollutant_cols.items():
            if original_col in df.columns:
                value = row[original_col]
                
                # Clean value (remove 'No data', convert to float)
                if pd.notna(value) and str(value) != 'No data':
                    try:
                        numeric_value = float(str(value).replace('ugm-3', '').strip())
                        
                        clean_data.append({
                            'date': row['Date'].strftime('%Y-%m-%d'),
                            'location': location,
                            'latitude': latitude,
                            'longitude': longitude,
                            'site_type': site_type,
                            'zone': zone,
                            'pollutant_type': clean_col,
                            'value': numeric_value,
                            'unit': 'ugm-3',
                            'status': 'N'  # All data shows 'N' status
                        })
                    except (ValueError, TypeError):
                        continue
    
    # Create DataFrame and save
    clean_df = pd.DataFrame(clean_data)
    clean_df.to_csv(output_file, index=False)
    
    print(f"Cleaned data saved to {output_file}")
    print(f"Original rows: {len(df)}, Clean records: {len(clean_df)}")
    print(f"Date range: {clean_df['date'].min()} to {clean_df['date'].max()}")
    
    return clean_df

if __name__ == "__main__":
    clean_df = clean_csv_data(
        "data/raw/8997590721 (1).csv", 
        "data/raw/8997590721.csv"
    )
    print("\nSample of cleaned data:")
    print(clean_df.head(10))