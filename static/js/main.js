// UAE Stock Tracker - JavaScript functionality

let currentTab = 'dfm';

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load DFM data by default
    refreshData('dfm');
});

// Tab switching
function showTab(exchange) {
    currentTab = exchange;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${exchange}-tab`).classList.add('active');
    
    // Load data if not already loaded
    const content = document.getElementById(`${exchange}-content`);
    if (content.style.display === 'none') {
        refreshData(exchange);
    }
}

// Refresh data for an exchange
function refreshData(exchange) {
    const loading = document.getElementById(`${exchange}-loading`);
    const content = document.getElementById(`${exchange}-content`);
    const error = document.getElementById(`${exchange}-error`);
    
    // Show loading state
    loading.style.display = 'block';
    content.style.display = 'none';
    error.style.display = 'none';
    
    // Fetch data
    fetch(`/api/${exchange}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayData(exchange, data);
                updateLastUpdate(exchange, data.timestamp);
                loading.style.display = 'none';
                content.style.display = 'block';
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(err => {
            console.error('Error fetching data:', err);
            loading.style.display = 'none';
            error.style.display = 'block';
            error.textContent = `Error: ${err.message}. Please try again later.`;
        });
}

// Display data
function displayData(exchange, data) {
    displaySummary(exchange, data.summary);
    displayRecommendations(exchange, data.recommendations);
    displayStocksTable(exchange, data.stocks);
}

// Display summary statistics
function displaySummary(exchange, summary) {
    document.getElementById(`${exchange}-total-capital`).textContent = 
        `AED ${formatNumber(summary.total_capital_aed)}`;
    document.getElementById(`${exchange}-per-stock`).textContent = 
        `AED ${formatNumber(summary.allocation_per_stock_aed)}`;
    document.getElementById(`${exchange}-stocks-to-buy`).textContent = 
        summary.num_stocks_to_buy;
    document.getElementById(`${exchange}-allocated`).textContent = 
        `AED ${formatNumber(summary.total_allocated_aed)}`;
}

// Display buy recommendations
function displayRecommendations(exchange, recommendations) {
    const container = document.getElementById(`${exchange}-recommendations`);
    
    if (recommendations.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 2rem;">No buy recommendations at this time.</p>';
        return;
    }
    
    container.innerHTML = recommendations.map(stock => `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <div>
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div class="stock-name">${stock.name}</div>
                </div>
                <div style="text-align: right;">
                    <div class="detail-value price-negative">${stock.pct_from_52w_high.toFixed(2)}%</div>
                    <div class="detail-label">from 52W High</div>
                </div>
            </div>
            <div class="recommendation-details">
                <div class="detail-item">
                    <span class="detail-label">Current Price</span>
                    <span class="detail-value">$${stock.current_price.toFixed(2)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Shares to Buy</span>
                    <span class="detail-value">${stock.shares_to_buy}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Cost (USD)</span>
                    <span class="detail-value">$${formatNumber(stock.total_cost_usd)}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Cost (AED)</span>
                    <span class="detail-value">AED ${formatNumber(stock.total_cost_aed)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

// Display all stocks table
function displayStocksTable(exchange, stocks) {
    const tbody = document.getElementById(`${exchange}-stocks-tbody`);
    
    if (stocks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center;">No stock data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = stocks.map(stock => {
        const meetsCriteria = stock.meets_criteria || false;
        const rowClass = meetsCriteria ? 'buy-signal' : '';
        const priceChangeClass = stock.pct_change_from_prev >= 0 ? 'price-positive' : 'price-negative';
        const pctFrom52wClass = stock.pct_from_52w_high >= 0 ? 'price-positive' : 'price-negative';
        
        return `
            <tr class="${rowClass}">
                <td><strong>${stock.symbol}</strong></td>
                <td>${stock.name}</td>
                <td>$${stock.current_price.toFixed(2)}</td>
                <td>$${stock.previous_close.toFixed(2)}</td>
                <td>$${stock['52_week_high'].toFixed(2)}</td>
                <td class="${pctFrom52wClass}">${stock.pct_from_52w_high.toFixed(2)}%</td>
                <td class="${priceChangeClass}">${stock.pct_change_from_prev >= 0 ? '+' : ''}${stock.pct_change_from_prev.toFixed(2)}%</td>
                <td>${stock.condition_a ? '<span class="badge badge-success">✓</span>' : '<span class="badge badge-danger">✗</span>'}</td>
                <td>${stock.condition_b ? '<span class="badge badge-success">✓</span>' : '<span class="badge badge-danger">✗</span>'}</td>
                <td>${meetsCriteria ? '<span class="badge badge-success">BUY</span>' : ''}</td>
            </tr>
        `;
    }).join('');
}

// Update last update timestamp
function updateLastUpdate(exchange, timestamp) {
    const date = new Date(timestamp);
    const formatted = date.toLocaleString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    document.getElementById(`${exchange}-last-update`).textContent = `Last updated: ${formatted}`;
}

// Format number with commas
function formatNumber(num) {
    return num.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}
