import yfinance as yf
import pandas as pd
from .base import DataFetcher

class YFinanceFetcher(DataFetcher):
    def get_stock_data(self, ticker: str, start_date: str = None, end_date: str = None, period: str = "1y") -> pd.DataFrame:
        """Fetch historical stock data using yfinance."""
        stock = yf.Ticker(ticker)
        if start_date and end_date:
            df = stock.history(start=start_date, end=end_date)
        else:
            df = stock.history(period=period)
        return df

    def get_real_time_quote(self, ticker: str) -> dict:
        """Fetch real-time stock quote using yfinance."""
        stock = yf.Ticker(ticker)
        
        last_price = None
        prev_close = None
        company_name = ticker
        
        try:
            fast = stock.fast_info
            last_price = fast.get('lastPrice')
            prev_close = fast.get('regularMarketPreviousClose') or fast.get('previousClose')
        except Exception as e:
            print(f"Fast info error for {ticker}: {e}")
            
        # Try to get info safely
        try:
            info = stock.info
            if isinstance(info, dict):
                company_name = info.get("longName") or ticker
                if last_price is None:
                    last_price = info.get("currentPrice") or info.get("regularMarketPrice")
                if prev_close is None:
                    prev_close = info.get("previousClose")
        except Exception as e:
            print(f"Info error for {ticker}: {e}")
            
        # Fallback to history if price still missing
        if last_price is None:
            try:
                hist = stock.history(period="1d")
                if not hist.empty:
                    last_price = hist['Close'].iloc[-1]
            except:
                pass
            
        change = None
        change_pct = None
        if last_price is not None and prev_close is not None:
            change = last_price - prev_close
            change_pct = (change / prev_close) if prev_close else 0
            
        return {
            "symbol": ticker,
            "company_name": company_name,
            "price": last_price,
            "change": change,
            "change_percent": change_pct,
            "volume": None, # Volume is less critical for basic quote
        }

    def get_fundamentals(self, ticker: str) -> dict:
        """Fetch fundamental data using yfinance."""
        stock = yf.Ticker(ticker)
        info = {}
        try:
            info = stock.info
            if not isinstance(info, dict): info = {}
        except Exception as e:
            print(f"Fundamentals info error for {ticker}: {e}")
        
        # Calculate revenue growth if possible, or use yfinance provided one
        rev_growth = info.get("revenueGrowth")
        
        return {
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "revenue_growth": rev_growth,
            "net_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "industry": info.get("industry"),
            "free_cash_flow": info.get("freeCashflow"),
            "fcf_growth": info.get("freeCashflowGrowth"),
            "beta": info.get("beta"),
            "current_ratio": info.get("currentRatio"),
            "institutional_ownership": info.get("heldPercentInstitutions"),
            "market_cap": info.get("marketCap"),
            "total_assets": info.get("totalAssets"),
            "total_liabilities": info.get("totalLiabilitiesNetMinorityInterest"),
            "ebit": info.get("ebitda"), # Use EBITDA as proxy if ebit missing
            "total_revenue": info.get("totalRevenue")
        }

    def get_analyst_recommendations(self, ticker: str) -> dict:
        """Fetch analyst recommendations using yfinance."""
        stock = yf.Ticker(ticker)
        info = {}
        try:
            info = stock.info
            if not isinstance(info, dict): info = {}
        except Exception as e:
            print(f"Analyst info error for {ticker}: {e}")
        return {
            "recommendation_key": info.get("recommendationKey") or "hold",
            "recommendation_mean": info.get("recommendationMean"),
            "target_mean_price": info.get("targetMeanPrice"),
            "number_of_analyst_opinions": info.get("numberOfAnalystOpinions"),
        }

    def get_institutional_holders(self, ticker: str) -> pd.DataFrame:
        """Fetch institutional holders using yfinance."""
        stock = yf.Ticker(ticker)
        return stock.institutional_holders

    def get_insider_transactions(self, ticker: str) -> pd.DataFrame:
        """Fetch insider transactions using yfinance."""
        stock = yf.Ticker(ticker)
        return stock.insider_transactions

    def get_insider_purchases(self, ticker: str) -> pd.DataFrame:
        """Fetch insider purchases summary using yfinance."""
        stock = yf.Ticker(ticker)
        return stock.insider_purchases
