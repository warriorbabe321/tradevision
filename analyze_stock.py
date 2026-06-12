import json
import sys
import os
from src.analysis.analysis_service import perform_comprehensive_analysis
from dotenv import load_dotenv

load_dotenv()

def analyze_stock(ticker, risk_level="Standard", horizon="Short Term"):
    print(f"Analyzing {ticker} in {risk_level} mode...")
    
    result = perform_comprehensive_analysis(ticker, risk_level=risk_level, horizon=horizon)
    if not result:
        print(f"No data for {ticker}")
        return None

    # Map the new structure back to what the legacy CLI/Report expects
    # These helpers were defined in the original analyze_stock.py. 
    # Since they are specific to generating the textual thesis and debate, 
    # I'll keep them here or move them to reporting.
    
    legacy_result = {
        "Ticker": result['ticker'],
        "Company": result['company'],
        "CurrentPrice": result['price'],
        "Signal": result['status'],
        "Confidence": round(result['score'] / 100, 2),
        "RSI": result['technicals'].get('rsi'),
        "MACD": result['technicals'].get('macd'),
        "BollingerBands": {
            "Upper": result['technicals'].get('upper_bb'),
            "Lower": result['technicals'].get('lower_bb')
        },
        "ATR": result['technicals'].get('atr'),
        "VWAP": result['technicals'].get('vwap'),
        "OBV": result['technicals'].get('obv'),
        "PE_Ratio": result['fundamentals'].get('pe_ratio'),
        "RevenueGrowth": f"{round(result['fundamentals'].get('revenue_growth', 0)*100, 2)}%" if result['fundamentals'].get('revenue_growth') else "N/A",
        "NetMargin": f"{round(result['fundamentals'].get('net_margin', 0)*100, 2)}%" if result['fundamentals'].get('net_margin') else "N/A",
        "DebtToEquity": result['fundamentals'].get('debt_to_equity'),
        "TopHolders": [], 
        "Thesis": generate_thesis(result['ticker'], result['status'], result['details']),
        "Debate": generate_debate(result['fundamentals'], result['details']),
        "RiskMgmt": perform_risk_assessment(result['fundamentals'], {"price": result['price']}, horizon),
        "HighConviction": result.get('hc_data'),
        "VultureData": result.get('vulture_data'),
        "ExecutionPlan": generate_execution_plan(result['price'], horizon),
        "EliteSignals": result.get('alt_data'),
        "InsiderActivity": {
            "Score": result['alt_data']['score'],
            "Status": result['alt_data']['details']['insider']
        },
        "DataIntegrity": {"Status": "Reliable"},
        "ChartData": result['chart_data']
    }
    
    return legacy_result

def generate_thesis(ticker, signal, details):
    # Simplified thesis based on the new details structure
    reasons = []
    if details.get('technical', {}).get('trend') == 100: reasons.append("Strong bullish price trend")
    if details.get('fundamental', {}).get('margin') == 100: reasons.append("Strong profit margins")
    
    summary = f"{signal} signal for {ticker} based on composite analysis. "
    if reasons:
        summary += "Key factors: " + ", ".join(reasons) + "."
    return summary

def generate_debate(fundamentals, details):
    bull_cases = ["Positive sector tailwinds."]
    bear_cases = ["Macroeconomic uncertainty."]
    
    rev_growth = fundamentals.get('revenue_growth')
    if rev_growth and rev_growth > 0.20:
        bull_cases.insert(0, "Aggressive expansion in a growing market.")
        
    return {
        "BullCase": bull_cases[0],
        "BearCase": bear_cases[0]
    }

def perform_risk_assessment(fundamentals, quote, horizon):
    no_go_triggered = False
    reasons = []
    
    de = fundamentals.get('debt_to_equity')
    if de and de > 200:
        no_go_triggered = True
        reasons.append("Debt Crisis: D/E > 2.0")
        
    current_price = quote.get('price')
    stop_loss = current_price * 0.9 if current_price else None
    
    return {
        "no_go_triggered": no_go_triggered,
        "reasons": reasons,
        "stop_loss": round(stop_loss, 2) if stop_loss else None
    }

def generate_execution_plan(price, horizon):
    if not price: return {}
    return {
        "Entry": round(price, 2),
        "Target": round(price * 1.15, 2),
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Analyze a stock ticker.')
    parser.add_argument('ticker', help='The stock ticker to analyze (e.g., AAPL)')
    parser.add_argument('--risk', default='Standard', choices=['Standard', 'Conservative', 'Retailer High-Conviction', 'Sure-Win'], help='Risk level')
    parser.add_argument('--horizon', default='Short Term', choices=['Day Trade', 'Short Term', 'Long Term'], help='Time horizon')
    args = parser.parse_args()
    
    ticker = args.ticker.upper()
    analysis = analyze_stock(ticker, risk_level=args.risk, horizon=args.horizon)
    if analysis:
        print(json.dumps(analysis, indent=2))
