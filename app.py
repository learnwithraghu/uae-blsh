"""
UAE Stock Tracker - Flask Web Application
Tracks investment opportunities in Dubai Financial Market (DFM) and Abu Dhabi Securities Exchange (ADX)
"""

from flask import Flask, render_template, jsonify, request
import logging
from datetime import datetime
import os

from src.config_loader import load_config
from src.data_fetcher import DFMDataFetcher, ADXDataFetcher
from src.stock_analyzer import StockAnalyzer
from src.gcs_storage import GCSStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Load configuration
try:
    config = load_config('config.yaml')
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load config: {e}")
    config = {
        'gcp': {'project_id': None, 'bucket_name': None},
        'investment': {
            'total_capital_aed': 50000,
            'allocation_per_stock_aed': 1250,
            'max_stocks_high_dip': 3,
            'max_stocks_low_dip': 1,
            'dip_threshold_percent': -10.0
        },
        'exchange_rate': {'usd_to_aed': 3.67},
        'stocks': {'dfm': [], 'adx': []}
    }

# Initialize components
dfm_fetcher = DFMDataFetcher()
adx_fetcher = ADXDataFetcher()
analyzer = StockAnalyzer(config['investment'])

# Initialize GCS storage (optional - will gracefully fail if not configured)
bucket_name = os.getenv('GCS_BUCKET', config['gcp'].get('bucket_name'))
project_id = os.getenv('GCP_PROJECT', config['gcp'].get('project_id'))

if bucket_name:
    storage = GCSStorage(bucket_name, project_id)
else:
    logger.warning("GCS bucket not configured, data will not be persisted")
    storage = None

# Cache for stock data
cache = {
    'dfm': {'data': None, 'timestamp': None},
    'adx': {'data': None, 'timestamp': None}
}


@app.route('/')
def index():
    """Home page showing both DFM and ADX."""
    return render_template('index.html')


@app.route('/api/dfm')
def get_dfm_data():
    """API endpoint for DFM stock data."""
    try:
        # Fetch stock data
        logger.info("Fetching DFM stock data...")
        dfm_symbols = config['stocks'].get('dfm', [])
        dfm_symbols = dfm_symbols if dfm_symbols else None
        
        dfm_data = dfm_fetcher.get_all_stocks(dfm_symbols)
        
        if dfm_data.empty:
            return jsonify({
                'success': False,
                'error': 'No DFM data available',
                'stocks': [],
                'recommendations': [],
                'summary': {}
            })
        
        # Analyze stocks
        exchange_rate = config['exchange_rate']['usd_to_aed']
        all_stocks, recommendations = analyzer.analyze_stocks(dfm_data, exchange_rate)
        summary = analyzer.get_summary_stats(recommendations)
        
        # Save to GCS
        if storage:
            storage.save_daily_snapshot('dfm', all_stocks)
            storage.save_buy_recommendations('dfm', recommendations, summary)
        
        # Update cache
        cache['dfm'] = {
            'data': {
                'all_stocks': all_stocks.to_dict(orient='records'),
                'recommendations': recommendations.to_dict(orient='records'),
                'summary': summary
            },
            'timestamp': datetime.now()
        }
        
        return jsonify({
            'success': True,
            'exchange': 'DFM',
            'stocks': all_stocks.to_dict(orient='records'),
            'recommendations': recommendations.to_dict(orient='records'),
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching DFM data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'stocks': [],
            'recommendations': [],
            'summary': {}
        }), 500


@app.route('/api/adx')
def get_adx_data():
    """API endpoint for ADX stock data."""
    try:
        # Fetch stock data
        logger.info("Fetching ADX stock data...")
        adx_symbols = config['stocks'].get('adx', [])
        adx_symbols = adx_symbols if adx_symbols else None
        
        adx_data = adx_fetcher.get_all_stocks(adx_symbols)
        
        if adx_data.empty:
            return jsonify({
                'success': False,
                'error': 'No ADX data available',
                'stocks': [],
                'recommendations': [],
                'summary': {}
            })
        
        # Analyze stocks
        exchange_rate = config['exchange_rate']['usd_to_aed']
        all_stocks, recommendations = analyzer.analyze_stocks(adx_data, exchange_rate)
        summary = analyzer.get_summary_stats(recommendations)
        
        # Save to GCS
        if storage:
            storage.save_daily_snapshot('adx', all_stocks)
            storage.save_buy_recommendations('adx', recommendations, summary)
        
        # Update cache
        cache['adx'] = {
            'data': {
                'all_stocks': all_stocks.to_dict(orient='records'),
                'recommendations': recommendations.to_dict(orient='records'),
                'summary': summary
            },
            'timestamp': datetime.now()
        }
        
        return jsonify({
            'success': True,
            'exchange': 'ADX',
            'stocks': all_stocks.to_dict(orient='records'),
            'recommendations': recommendations.to_dict(orient='records'),
            'summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching ADX data: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'stocks': [],
            'recommendations': [],
            'summary': {}
        }), 500


@app.route('/health')
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # For local development
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
