# UAE Stock Tracker

A modern web application for tracking stock investment opportunities in the Dubai Financial Market (DFM) and Abu Dhabi Securities Exchange (ADX). Built with Flask and deployed on Google Cloud Run.

## 🎯 Features

- **Dual Exchange Support**: Track stocks from both DFM and ADX
- **Dip-Buy Trailing Strategy**: Automatically identifies buy opportunities based on:
  - Stocks fallen from 52-week highs
  - Trading above previous day's close
  - Smart allocation (1-3 stocks based on market conditions)
- **Real-time Data**: Fetches live stock prices from investing.com
- **Modern UI**: Clean, responsive interface with dark mode and animations
- **Cloud Storage**: Saves daily snapshots and analysis to GCS
- **Auto-scaling**: Deployed on Cloud Run for reliability

## 📊 Investment Strategy

### Capital Allocation
- **Total Capital**: AED 50,000
- **Per Stock**: AED 1,250 (40 equal parts)

### Buy Conditions
A stock must meet **both** conditions:
1. **Condition A**: Stock has fallen from its 52-week high
2. **Condition B**: Stock is trading above previous day's close

### Buy Algorithm
- If top stock dropped **> 10%** from 52W high → Buy up to **3 stocks**
- If top stock dropped **≤ 10%** from 52W high → Buy only **1 stock**

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- GCP account with Cloud Run enabled
- GCS bucket for data storage

### Local Development

1. **Clone and setup**:
```bash
cd /path/to/uae-blsh
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure settings**:
Edit `config.yaml` with your GCP details:
```yaml
gcp:
  project_id: "your-gcp-project-id"
  region: "me-west1"
  bucket_name: "your-bucket-name"
```

3. **Run locally**:
```bash
python app.py
```

4. **Open browser**: http://localhost:8080

### GCP Deployment

#### Option 1: Using Cloud Build (Recommended)

1. **Update Cloud Build configuration**:
Edit `cloudbuild.yaml` and update substitutions:
```yaml
substitutions:
  _REGION: 'me-west1'  # Your region
  _GCS_BUCKET: 'your-actual-bucket-name'
```

2. **Submit build**:
```bash
gcloud builds submit --config cloudbuild.yaml
```

3. **Access your app**:
```bash
gcloud run services describe uae-stock-tracker \
  --region=me-west1 \
  --format='value(status.url)'
```

#### Option 2: Manual Deployment

1. **Build Docker image**:
```bash
docker build -t gcr.io/YOUR_PROJECT_ID/uae-stock-tracker:latest .
```

2. **Push to GCR**:
```bash
docker push gcr.io/YOUR_PROJECT_ID/uae-stock-tracker:latest
```

3. **Deploy to Cloud Run**:
```bash
gcloud run deploy uae-stock-tracker \
  --image gcr.io/YOUR_PROJECT_ID/uae-stock-tracker:latest \
  --region me-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCS_BUCKET=your-bucket-name,GCP_PROJECT=YOUR_PROJECT_ID
```

## 📁 Project Structure

```
uae-blsh/
├── app.py                  # Flask application
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker configuration
├── cloudbuild.yaml         # Cloud Build CI/CD
├── src/
│   ├── data_fetcher.py     # Stock data fetching
│   ├── stock_analyzer.py   # Investment analysis logic
│   ├── gcs_storage.py      # Cloud Storage integration
│   └── config_loader.py    # Config helper
├── templates/
│   └── index.html          # Web UI template
└── static/
    ├── css/
    │   └── style.css       # Styles
    └── js/
        └── main.js         # Client-side logic
```

## 🔧 Configuration

### Environment Variables (Cloud Run)
- `GCS_BUCKET`: GCS bucket name for data persistence
- `GCP_PROJECT`: GCP project ID
- `PORT`: Server port (default: 8080)

### Config File (`config.yaml`)
- **GCP settings**: Project ID, region, bucket
- **Investment parameters**: Capital, allocation, thresholds
- **Exchange rate**: USD to AED
- **Stock lists**: Optional custom stock symbols

## 📈 Data Sources

- **Primary**: investing.com (web scraping)
- **Fallback**: Dubai Pulse API for DFM indices
- **Update Frequency**: On-demand via UI refresh button

## 🔒 Security Notes

⚠️ **Important**: 
- The app allows **unauthenticated access** (public) as specified
- Cloud Run service account needs Storage Object Admin role for GCS
- Never commit sensitive credentials to Git

## 🛠️ Troubleshooting

### Data Not Loading
1. Check browser console for errors
2. Verify stock URLs in `src/data_fetcher.py` are still valid
3. investing.com may have rate limits - wait a few minutes

### Cloud Run Deployment Issues
1. Ensure service account has proper GCS permissions:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member=serviceAccount:YOUR_SA@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

2. Check Cloud Run logs:
```bash
gcloud run services logs read uae-stock-tracker --region=me-west1
```

### Local Development
- Set `GOOGLE_APPLICATION_CREDENTIALS` for GCS:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## 📝 License

MIT License - Feel free to use and modify

## ⚠️ Disclaimer

**This application is for informational and educational purposes only.**

- Not financial advice
- Stock prices may be delayed
- Always perform your own research
- Past performance doesn't guarantee future results
- Consult a financial advisor before making investment decisions

## 🤝 Contributing

Suggestions and improvements welcome! Key areas:
- Additional data sources
- More exchange support
- Enhanced strategies
- UI improvements

---

**Built with ❤️ for UAE Stock Market Enthusiasts**
