"""GCS storage module for saving stock data and analysis results."""

from google.cloud import storage
import pandas as pd
import json
from datetime import datetime
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class GCSStorage:
    """Handles data persistence to Google Cloud Storage."""
    
    def __init__(self, bucket_name: str, project_id: Optional[str] = None):
        """
        Initialize GCS client.
        
        Args:
            bucket_name: Name of the GCS bucket
            project_id: GCP project ID (optional, uses default credentials)
        """
        self.bucket_name = bucket_name
        self.project_id = project_id
        
        # Initialize storage client
        # In Cloud Run, this will use the service account automatically
        # In local development, set GOOGLE_APPLICATION_CREDENTIALS env var
        try:
            if project_id:
                self.client = storage.Client(project=project_id)
            else:
                self.client = storage.Client()
            
            self.bucket = self.client.bucket(bucket_name)
            logger.info(f"Initialized GCS client for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            self.client = None
            self.bucket = None
    
    def save_daily_snapshot(self, exchange: str, df: pd.DataFrame) -> bool:
        """
        Save daily stock snapshot to GCS.
        
        Args:
            exchange: Exchange name (dfm or adx)
            df: DataFrame with stock data
        
        Returns:
            True if successful, False otherwise
        """
        if self.bucket is None:
            logger.warning("GCS client not initialized, skipping save")
            return False
        
        try:
            # Create filename with date
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"snapshots/{exchange}/{date_str}.csv"
            
            # Convert DataFrame to CSV
            csv_data = df.to_csv(index=False)
            
            # Upload to GCS
            blob = self.bucket.blob(filename)
            blob.upload_from_string(csv_data, content_type='text/csv')
            
            logger.info(f"Saved snapshot to gs://{self.bucket_name}/{filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False
    
    def save_buy_recommendations(self, exchange: str, recommendations: pd.DataFrame, 
                                 summary: dict) -> bool:
        """
        Save buy recommendations to GCS.
        
        Args:
            exchange: Exchange name (dfm or adx)
            recommendations: DataFrame with buy recommendations
            summary: Summary statistics dict
        
        Returns:
            True if successful, False otherwise
        """
        if self.bucket is None:
            logger.warning("GCS client not initialized, skipping save")
            return False
        
        try:
            # Create filename with datetime
            datetime_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"recommendations/{exchange}/{datetime_str}.json"
            
            # Prepare data
            data = {
                'timestamp': datetime.now().isoformat(),
                'exchange': exchange,
                'summary': summary,
                'recommendations': recommendations.to_dict(orient='records') if not recommendations.empty else []
            }
            
            # Upload to GCS
            blob = self.bucket.blob(filename)
            blob.upload_from_string(json.dumps(data, indent=2), content_type='application/json')
            
            logger.info(f"Saved recommendations to gs://{self.bucket_name}/{filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save recommendations: {e}")
            return False
    
    def load_latest_snapshot(self, exchange: str) -> Optional[pd.DataFrame]:
        """
        Load the most recent snapshot for an exchange.
        
        Args:
            exchange: Exchange name (dfm or adx)
        
        Returns:
            DataFrame if found, None otherwise
        """
        if self.bucket is None:
            logger.warning("GCS client not initialized")
            return None
        
        try:
            # List all snapshots for this exchange
            prefix = f"snapshots/{exchange}/"
            blobs = list(self.bucket.list_blobs(prefix=prefix))
            
            if not blobs:
                logger.info(f"No snapshots found for {exchange}")
                return None
            
            # Get the most recent blob
            latest_blob = max(blobs, key=lambda b: b.updated)
            
            # Download and parse CSV
            csv_data = latest_blob.download_as_text()
            df = pd.read_csv(pd.io.common.StringIO(csv_data))
            
            logger.info(f"Loaded snapshot from gs://{self.bucket_name}/{latest_blob.name}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to load snapshot: {e}")
            return None
