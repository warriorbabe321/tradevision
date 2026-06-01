from flask import Flask, render_template, request, redirect, url_for, session
import os
import yfinance as yf
import pandas as pd
from functools import wraps
import requests

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response
app.secret_key = "tradevision-key-2026"

# STEALTH MODE: Prevents rate-limiting
session_requests = requests.Session()
session_requests.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

def require_access_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_key' not in session: return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@require_access_key
def dashboard():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
@require_access_key
def analyze():
    ticker = request.form.get("ticker").upper()
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return f"No data for {ticker}"

        # Calculate SMAs
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        
        # Calculate RSI (14-period)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # Calculate MACD (12, 26, 9)
        exp1 = hist['Close'].ewm(span=12, adjust=False).mean()
        exp2 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = exp1 - exp2
        hist['MACD_signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # Get current price safely
        try:
            current_price = stock.fast_info.get('lastPrice') or stock.fast_info.get('regularMarketPrice')
            if current_price is None:
                current_price = hist['Close'].iloc[-1]
        except Exception:
            current_price = hist['Close'].iloc[-1]

        # Get SMAs with safety checks
        def get_last_valid(series):
            return series.iloc[-1] if not series.empty and not pd.isna(series.iloc[-1]) else 0

        s20 = get_last_valid(hist['SMA20'])
        s50 = get_last_valid(hist['SMA50'])
        s200 = get_last_valid(hist['SMA200'])
        
        # Perfect Alignment Logic (Golden Zone: Price > 20 > 50 > 200)
        is_perfect = (current_price > s20 > s50 > s200) if (s20 and s50 and s200) else False
        
        # Get fundamentals safely
        try:
            info = stock.info
            if not isinstance(info, dict): info = {}
        except Exception:
            info = {}

        score = 0
        if info.get('debtToEquity', 100) < 50: score += 40
        if info.get('profitMargins', 0) > 0.10: score += 30
        if info.get('operatingCashflow', 0) > 0: score += 30

        # Determine status - Retail Gold when perfect alignment AND strong fundamentals
        is_retail_gold = is_perfect and score >= 70
        
        result = {
            "ticker": ticker,
            "price": round(current_price, 2) if current_price else 0.0,
            "score": score,
            "status": "RETAIL GOLD" if is_retail_gold else "NEUTRAL",
            "alignment": "PERFECT" if is_perfect else "UNALIGNED"
        }
        
        return render_template("scanner.html", stocks=[result])
    except Exception as e:
        return f"System Busy. Try again in a moment. ({str(e)})"

@app.route("/safety_scanner")
@require_access_key
def scanner():
    # Example Gold Wins
    stocks = [{"ticker": "BRK-B", "score": 100, "status": "Retail Gold"}, {"ticker": "GOOGL", "score": 85, "status": "Retail Gold"}]
    return render_template("scanner.html", stocks=stocks)

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        if request.form.get("access_key") == "gold-investor-2026":
            session['access_key'] = "gold-investor-2026"
            return redirect(url_for('dashboard'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
# Trigger deploy
# Deploy trigger: Mon Jun  1 14:20:16 UTC 2026
