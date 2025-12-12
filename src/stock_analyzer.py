"""Stock analysis module implementing the dip-buy trailing strategy."""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """
    Analyzes stocks based on dip-buy trailing strategy.
    
    Strategy:
    - Buy stocks that have fallen from 52-week high (Condition A)
    - AND are trading above previous day's close (Condition B)
    - Buy 1-3 stocks depending on how much the top stock has dropped
    """
    
    def __init__(self, config: Dict):
        """
        Initialize analyzer with investment configuration.
        
        Args:
            config: Investment configuration dict with keys:
                - total_capital_aed: Total capital in AED
                - allocation_per_stock_aed: Amount to invest per stock
                - max_stocks_high_dip: Max stocks to buy if top stock dropped > threshold
                - max_stocks_low_dip: Max stocks to buy if top stock dropped <= threshold
                - dip_threshold_percent: Threshold (e.g., -10.0)
        """
        self.total_capital = config.get('total_capital_aed', 50000)
        self.allocation_per_stock = config.get('allocation_per_stock_aed', 1250)
        self.max_stocks_high_dip = config.get('max_stocks_high_dip', 3)
        self.max_stocks_low_dip = config.get('max_stocks_low_dip', 1)
        self.dip_threshold = config.get('dip_threshold_percent', -10.0)
    
    def analyze_stocks(self, df: pd.DataFrame, exchange_rate: float = 3.67) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Analyze stocks and generate buy recommendations.
        
        Args:
            df: DataFrame with columns: symbol, name, current_price, previous_close, 52_week_high
            exchange_rate: USD to AED exchange rate
        
        Returns:
            Tuple of (all_stocks_df, buy_recommendations_df)
        """
        if df.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Calculate derived metrics
        df = df.copy()
        df['pct_from_52w_high'] = ((df['current_price'] - df['52_week_high']) / df['52_week_high'] * 100)
        df['pct_change_from_prev'] = ((df['current_price'] - df['previous_close']) / df['previous_close'] * 100)
        
        # Check conditions
        df['condition_a'] = df['current_price'] < df['52_week_high']  # Fallen from 52W high
        df['condition_b'] = df['current_price'] > df['previous_close']  # Above previous close
        df['meets_criteria'] = df['condition_a'] & df['condition_b']
        
        # Sort by % from 52-week high (most negative first = biggest dip)
        df = df.sort_values('pct_from_52w_high', ascending=True)
        
        # Determine how many stocks to buy
        buy_candidates = df[df['meets_criteria']].copy()
        
        if buy_candidates.empty:
            logger.info("No stocks meet buy criteria")
            return df, pd.DataFrame()
        
        # Check top stock's drop percentage
        top_stock_drop = buy_candidates.iloc[0]['pct_from_52w_high']
        
        if top_stock_drop < self.dip_threshold:  # e.g., dropped more than -10%
            max_buys = self.max_stocks_high_dip
        else:
            max_buys = self.max_stocks_low_dip
        
        # Select stocks to buy
        buy_recommendations = buy_candidates.head(max_buys).copy()
        
        # Calculate investment details
        buy_recommendations['investment_aed'] = self.allocation_per_stock
        buy_recommendations['investment_usd'] = buy_recommendations['investment_aed'] / exchange_rate
        buy_recommendations['shares_to_buy'] = np.floor(
            buy_recommendations['investment_usd'] / buy_recommendations['current_price']
        ).astype(int)
        buy_recommendations['total_cost_usd'] = (
            buy_recommendations['shares_to_buy'] * buy_recommendations['current_price']
        )
        buy_recommendations['total_cost_aed'] = buy_recommendations['total_cost_usd'] * exchange_rate
        
        logger.info(f"Top stock drop: {top_stock_drop:.2f}%, recommending {len(buy_recommendations)} stocks")
        
        return df, buy_recommendations
    
    def get_summary_stats(self, buy_recommendations: pd.DataFrame) -> Dict:
        """
        Calculate summary statistics for display.
        
        Args:
            buy_recommendations: DataFrame of stocks to buy
        
        Returns:
            Dict with summary statistics
        """
        num_stocks = len(buy_recommendations)
        total_allocated = num_stocks * self.allocation_per_stock
        available_capital = self.total_capital - total_allocated
        
        return {
            'total_capital_aed': self.total_capital,
            'allocation_per_stock_aed': self.allocation_per_stock,
            'num_stocks_to_buy': num_stocks,
            'total_allocated_aed': total_allocated,
            'available_capital_aed': available_capital,
            'total_actual_cost_aed': buy_recommendations['total_cost_aed'].sum() if not buy_recommendations.empty else 0
        }
