"""
Data fetching module for UAE stock exchanges (DFM and ADX).
Fetches stock data from investing.com and Dubai Pulse API.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DFMDataFetcher:
    """Fetches data for Dubai Financial Market (DFM) stocks."""
    
    # Major DFM stocks with their investing.com URLs
    DFM_STOCKS = {
        'DFM': {'name': 'Dubai Financial Market', 'url': 'https://www.investing.com/equities/dfm'},
        'EMAAR': {'name': 'Emaar Properties', 'url': 'https://www.investing.com/equities/emaar-properties'},
        'DIB': {'name': 'Dubai Islamic Bank', 'url': 'https://www.investing.com/equities/dubai-islamic-bank'},
        'ARABTECH': {'name': 'Arabtec Holding', 'url': 'https://www.investing.com/equities/arabtec-holding'},
        'DEWA': {'name': 'Dubai Electricity & Water', 'url': 'https://www.investing.com/equities/dewa'},
        'EMAARDEV': {'name': 'Emaar Development', 'url': 'https://www.investing.com/equities/emaar-development'},
        'TAKAFUL': {'name': 'Dubai Islamic Insurance', 'url': 'https://www.investing.com/equities/dubai-islamic-insurance'},
        'GFH': {'name': 'GFH Financial Group', 'url': 'https://www.investing.com/equities/gfh-financial-group'},
        'DAMAC': {'name': 'Damac Properties', 'url': 'https://www.investing.com/equities/damac-properties'},
        'AMANAT': {'name': 'Amanat Holdings', 'url': 'https://www.investing.com/equities/amanat-holdings'},
    }
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def fetch_stock_data(self, symbol: str, stock_info: Dict) -> Optional[Dict]:
        """Fetch current price, previous close, and 52-week high for a stock."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(stock_info['url'], headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Try to extract price data from investing.com page
                # Note: Structure may change, this is a best-effort implementation
                current_price = self._extract_current_price(soup)
                previous_close = self._extract_previous_close(soup)
                week_52_high = self._extract_52week_high(soup)
                
                if current_price is not None:
                    return {
                        'symbol': symbol,
                        'name': stock_info['name'],
                        'current_price': current_price,
                        'previous_close': previous_close or current_price,
                        '52_week_high': week_52_high or current_price,
                        'last_updated': datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Could not extract price for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching {symbol} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def _extract_current_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current price from page."""
        try:
            # Try multiple selectors as investing.com structure varies
            price_elem = soup.find('span', {'data-test': 'instrument-price-last'})
            if not price_elem:
                price_elem = soup.find('span', class_='text-2xl')
            if not price_elem:
                price_elem = soup.select_one('[class*="instrument-price"]')
            
            if price_elem:
                price_text = price_elem.text.strip().replace(',', '')
                return float(price_text)
        except Exception as e:
            logger.debug(f"Price extraction error: {e}")
        return None
    
    def _extract_previous_close(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract previous close from page."""
        try:
            # Look for "Prev. Close" label
            labels = soup.find_all('dt', class_='text-left')
            for label in labels:
                if 'Prev. Close' in label.text or 'Previous Close' in label.text:
                    value_elem = label.find_next_sibling('dd')
                    if value_elem:
                        value_text = value_elem.text.strip().replace(',', '')
                        return float(value_text)
        except Exception as e:
            logger.debug(f"Previous close extraction error: {e}")
        return None
    
    def _extract_52week_high(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract 52-week high from page."""
        try:
            # Look for "52 wk High" label
            labels = soup.find_all('dt', class_='text-left')
            for label in labels:
                if '52' in label.text and 'High' in label.text:
                    value_elem = label.find_next_sibling('dd')
                    if value_elem:
                        value_text = value_elem.text.strip().replace(',', '')
                        return float(value_text)
        except Exception as e:
            logger.debug(f"52-week high extraction error: {e}")
        return None
    
    def get_all_stocks(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch data for all DFM stocks.
        
        Args:
            symbols: Optional list of symbols to fetch. If None, fetches all.
        
        Returns:
            DataFrame with stock data
        """
        stocks_to_fetch = symbols if symbols else list(self.DFM_STOCKS.keys())
        results = []
        
        for symbol in stocks_to_fetch:
            if symbol not in self.DFM_STOCKS:
                logger.warning(f"Unknown DFM symbol: {symbol}")
                continue
            
            stock_info = self.DFM_STOCKS[symbol]
            logger.info(f"Fetching DFM: {symbol} ({stock_info['name']})")
            
            data = self.fetch_stock_data(symbol, stock_info)
            if data:
                results.append(data)
            
            # Be respectful with requests
            time.sleep(0.5)
        
        if results:
            return pd.DataFrame(results)
        else:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['symbol', 'name', 'current_price', 'previous_close', '52_week_high', 'last_updated'])


class ADXDataFetcher:
    """Fetches data for Abu Dhabi Securities Exchange (ADX) stocks."""
    
    # Major ADX stocks with their investing.com URLs
    ADX_STOCKS = {
        'FAB': {'name': 'First Abu Dhabi Bank', 'url': 'https://www.investing.com/equities/fab'},
        'ADCB': {'name': 'Abu Dhabi Commercial Bank', 'url': 'https://www.investing.com/equities/adcb'},
        'ALDAR': {'name': 'Aldar Properties', 'url': 'https://www.investing.com/equities/aldar-properties'},
        'TAQA': {'name': 'Abu Dhabi National Energy', 'url': 'https://www.investing.com/equities/taqa'},
        'ADNOCDIST': {'name': 'ADNOC Distribution', 'url': 'https://www.investing.com/equities/adnoc-distribution'},
        'ADNOCDRILL': {'name': 'ADNOC Drilling', 'url': 'https://www.investing.com/equities/adnoc-drilling'},
        'ADNHC': {'name': 'Abu Dhabi National Hotels', 'url': 'https://www.investing.com/equities/adnhc'},
        'ALPHAMENA': {'name': 'Alpha Dhabi Holding', 'url': 'https://www.investing.com/equities/alpha-dhabi'},
        'ADPORTS': {'name': 'AD Ports Group', 'url': 'https://www.investing.com/equities/ad-ports'},
        'MULTIPLY': {'name': 'Multiply Group', 'url': 'https://www.investing.com/equities/multiply-group'},
    }
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    def fetch_stock_data(self, symbol: str, stock_info: Dict) -> Optional[Dict]:
        """Fetch current price, previous close, and 52-week high for a stock."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(stock_info['url'], headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'lxml')
                
                current_price = self._extract_current_price(soup)
                previous_close = self._extract_previous_close(soup)
                week_52_high = self._extract_52week_high(soup)
                
                if current_price is not None:
                    return {
                        'symbol': symbol,
                        'name': stock_info['name'],
                        'current_price': current_price,
                        'previous_close': previous_close or current_price,
                        '52_week_high': week_52_high or current_price,
                        'last_updated': datetime.now().isoformat()
                    }
                else:
                    logger.warning(f"Could not extract price for {symbol}")
                    
            except Exception as e:
                logger.error(f"Error fetching {symbol} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
        
        return None
    
    def _extract_current_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract current price from page."""
        try:
            price_elem = soup.find('span', {'data-test': 'instrument-price-last'})
            if not price_elem:
                price_elem = soup.find('span', class_='text-2xl')
            if not price_elem:
                price_elem = soup.select_one('[class*="instrument-price"]')
            
            if price_elem:
                price_text = price_elem.text.strip().replace(',', '')
                return float(price_text)
        except Exception as e:
            logger.debug(f"Price extraction error: {e}")
        return None
    
    def _extract_previous_close(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract previous close from page."""
        try:
            labels = soup.find_all('dt', class_='text-left')
            for label in labels:
                if 'Prev. Close' in label.text or 'Previous Close' in label.text:
                    value_elem = label.find_next_sibling('dd')
                    if value_elem:
                        value_text = value_elem.text.strip().replace(',', '')
                        return float(value_text)
        except Exception as e:
            logger.debug(f"Previous close extraction error: {e}")
        return None
    
    def _extract_52week_high(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract 52-week high from page."""
        try:
            labels = soup.find_all('dt', class_='text-left')
            for label in labels:
                if '52' in label.text and 'High' in label.text:
                    value_elem = label.find_next_sibling('dd')
                    if value_elem:
                        value_text = value_elem.text.strip().replace(',', '')
                        return float(value_text)
        except Exception as e:
            logger.debug(f"52-week high extraction error: {e}")
        return None
    
    def get_all_stocks(self, symbols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fetch data for all ADX stocks.
        
        Args:
            symbols: Optional list of symbols to fetch. If None, fetches all.
        
        Returns:
            DataFrame with stock data
        """
        stocks_to_fetch = symbols if symbols else list(self.ADX_STOCKS.keys())
        results = []
        
        for symbol in stocks_to_fetch:
            if symbol not in self.ADX_STOCKS:
                logger.warning(f"Unknown ADX symbol: {symbol}")
                continue
            
            stock_info = self.ADX_STOCKS[symbol]
            logger.info(f"Fetching ADX: {symbol} ({stock_info['name']})")
            
            data = self.fetch_stock_data(symbol, stock_info)
            if data:
                results.append(data)
            
            # Be respectful with requests
            time.sleep(0.5)
        
        if results:
            return pd.DataFrame(results)
        else:
            return pd.DataFrame(columns=['symbol', 'name', 'current_price', 'previous_close', '52_week_high', 'last_updated'])
