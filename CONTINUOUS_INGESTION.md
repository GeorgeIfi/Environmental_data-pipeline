# Continuous Data Ingestion Guide

## Landing Zone Structure

```
environmental-data/
├── landing/           # New raw files go here
│   ├── 2026-01-13/
│   ├── 2026-01-14/
│   └── ...
├── raw/              # Processed raw files
├── bronze/           # Ingested data
├── silver/           # Cleaned data  
└── gold/             # Analytics data
```

## Upload New Data

### Method 1: Azure CLI
```bash
az storage blob upload \
  --account-name stenvpipelinenm5piaoe \
  --container-name environmental-data \
  --name landing/$(date +%Y-%m-%d)/environmental_data.csv \
  --file your_new_file.csv
```

### Method 2: Azure Portal
1. Go to Storage Account → Containers → environmental-data
2. Navigate to `landing/` folder
3. Create folder with today's date: `2026-01-13`
4. Upload CSV files

### Method 3: Automated Upload Script
```bash
# Create upload script
./upload_new_data.sh your_file.csv
```

## Trigger Pipeline Processing

### Manual Trigger:
```bash
az datafactory pipeline create-run \
  --factory-name adf-environmental-nm5piaoe \
  --resource-group rg-envpipeline-dev \
  --pipeline-name EnvironmentalDataPipeline \
  --parameters "inputPath=landing/2026-01-13/environmental_data.csv"
```

### Automated Trigger:
- ADF monitors `landing/` folder
- Automatically processes new files
- Moves processed files to `raw/`

## File Naming Convention

**Recommended format:**
```
environmental_data_YYYYMMDD_HHMMSS.csv
environmental_data_20260113_143000.csv
```

## Data Schema Requirements

New CSV files must have these columns:
- date (YYYY-MM-DD format)
- location
- latitude, longitude  
- site_type, zone
- pollutant_type
- value
- unit
- status

## Processing Flow

```
New File → landing/ → ADF Trigger → Pipeline → bronze/ → silver/ → gold/
```