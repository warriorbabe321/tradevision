import json
import pandas as pd
import yfinance as yf
from src.data_fetcher.yfinance_fetcher import YFinanceFetcher
from src.data_fetcher.alphavantage_fetcher import AlphaVantageFetcher
from src.data_fetcher.alternative_data_fetcher import AlternativeDataFetcher
from src.indicators.technical import (
    calculate_sma, calculate_rsi, calculate_macd,
    calculate_bollinger_bands, calculate_atr, calculate_vwap, calculate_obv,
    calculate_rvol, identify_hammer, identify_doji, calculate_mfi
)
from src.analysis.scoring_engine import ScoringEngine
import os

def perform_comprehensive_analysis(ticker, risk_level="Standard", horizon="Short Term"):
    yf_fetcher = YFinanceFetcher()
    av_fetcher = AlphaVantageFetcher()
    alt_fetcher = AlternativeDataFetcher()
    
    # Map UI "Sure-Win" to "Retailer High-Conviction" for the engine
    internal_risk = "Retailer High-Conviction" if risk_level == "Sure-Win" else risk_level
    scoring_engine = ScoringEngine(risk_level=internal_risk, horizon=horizon)

    # 1. Fetch Data
    try:
        hist_data = yf_fetcher.get_stock_data(ticker, period="1y")
        if hist_data.empty:
            return None

        quote = yf_fetcher.get_real_time_quote(ticker)
        fundamentals = yf_fetcher.get_fundamentals(ticker)
        recommendations = yf_fetcher.get_analyst_recommendations(ticker)
        inst_holders = yf_fetcher.get_institutional_holders(ticker)
        
        # News sentiment
        news_sentiment = av_fetcher.get_news_sentiment(ticker)
        
        # Insider & Alternative Data
        insider_purchases = yf_fetcher.get_insider_purchases(ticker)
        politician_trades = alt_fetcher.get_politician_trades(ticker)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

    # 2. Calculate Technicals
    sma20 = calculate_sma(hist_data, 20).iloc[-1]
    sma50 = calculate_sma(hist_data, 50).iloc[-1]
    sma200 = calculate_sma(hist_data, 200).iloc[-1]
    rsi = calculate_rsi(hist_data, 14).iloc[-1]
    macd_line, signal_line = calculate_macd(hist_data)
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    
    upper_bb, mid_bb, lower_bb = calculate_bollinger_bands(hist_data)
    atr = calculate_atr(hist_data).iloc[-1]
    vwap = calculate_vwap(hist_data).iloc[-1]
    obv = calculate_obv(hist_data).iloc[-1]
    rvol = calculate_rvol(hist_data).iloc[-1]
    is_hammer = identify_hammer(hist_data).iloc[-1]
    is_doji = identify_doji(hist_data).iloc[-1]

    current_price = quote['price']
    
    # Technical Summary for scoring
    tech_summary = {
        'price': current_price,
        'sma20': sma20,
        'sma50': sma50,
        'sma200': sma200,
        'rsi': rsi,
        'rvol': rvol,
        'hammer': is_hammer,
        'doji': is_doji,
        'macd': macd_val,
        'macd_signal': signal_val,
        'lower_bb': lower_bb.iloc[-1] if not lower_bb.empty else None,
        'upper_bb': upper_bb.iloc[-1] if not upper_bb.empty else None,
        'mfi': calculate_mfi(hist_data).iloc[-1],
        'vwap': vwap,
        'atr': atr,
        'volume_exhaustion': is_hammer or is_doji
    }

    t_score, t_details = scoring_engine.calculate_technical_score(
        current_price, sma50, sma200, rsi, macd_val, signal_val
    )

    # 3. Calculate Fundamentals
    f_score, f_details = scoring_engine.calculate_fundamental_score(
        fundamentals['pe_ratio'],
        fundamentals['peg_ratio'],
        fundamentals['revenue_growth'],
        fundamentals['net_margin'],
        fundamentals['debt_to_equity']
    )

    # 4. Calculate Sentiment
    s_score, s_details = scoring_engine.calculate_sentiment_score(
        recommendations['recommendation_key'],
        news_sentiment
    )
    
    # 4.1 Panic & Vulture Check
    panic_triggered, panic_triggers = scoring_engine.check_panic_signal(hist_data, tech_summary)
    vulture_data = None
    if panic_triggered:
        v_score, v_details = scoring_engine.calculate_vulture_score(fundamentals, tech_summary)
        v_verdict = "Vulture Buy" if v_score >= 80 else "Speculative Watch" if v_score >= 50 else "Falling Knife"
        vulture_data = {
            "Score": v_score,
            "Details": v_details,
            "Verdict": v_verdict,
            "PanicTriggers": panic_triggers
        }
        
    # 4.2 Insider & Alternative Scan
    alt_score, alt_details = scoring_engine.calculate_alternative_score(insider_purchases, politician_trades)

    # 5. Composite Score & Verdict
    composite_score = scoring_engine.get_composite_score(t_score, f_score, s_score)
    final_signal = scoring_engine.get_signal(composite_score)

    # Vulture Override
    strategy = "Standard"
    score = composite_score
    details = {"technical": t_details, "fundamental": f_details, "sentiment": s_details}
    
    if vulture_data:
        final_signal = f"VULTURE: {vulture_data['Verdict']}"
        strategy = "Vulture"
        score = vulture_data['Score']
        details = vulture_data['Details']

    # Handle Retailer High-Conviction Mode
    hc_data = None
    if internal_risk == "Retailer High-Conviction":
        hc_score, hc_details = scoring_engine.calculate_hc_score(fundamentals, tech_summary, recommendations)
        passes_filters, filter_fails = scoring_engine.check_hc_hard_filters(fundamentals, tech_summary, recommendations)
        
        hc_verdict = "AVOID / NOT PICKY ENOUGH"
        if passes_filters:
            is_perfect = (current_price > sma20 > sma50 > sma200)
            if hc_score >= 95 and is_perfect: hc_verdict = "SURE-WIN / RETAIL GOLD"
            elif hc_score >= 85: hc_verdict = "HIGH CONVICTION BUY"
            elif hc_score >= 75: hc_verdict = "STANDARD BUY"
        
        hc_data = {
            "Score": hc_score,
            "Details": hc_details,
            "PassesFilters": passes_filters,
            "FilterFails": filter_fails,
            "Verdict": hc_verdict
        }
        final_signal = hc_verdict
        strategy = "Retailer"
        score = hc_score
        details = hc_details

    # Prepare historical data for charts
    chart_data = []
    sma20_hist = calculate_sma(hist_data, 20)
    sma50_hist = calculate_sma(hist_data, 50)
    sma200_hist = calculate_sma(hist_data, 200)
    rsi_hist = calculate_rsi(hist_data, 14)
    macd_line_hist, signal_line_hist = calculate_macd(hist_data)
    upper_bb_hist, _, lower_bb_hist = calculate_bollinger_bands(hist_data)

    for i, (date, row) in enumerate(hist_data.iterrows()):
        chart_data.append({
            "time": date.strftime('%Y-%m-%d'),
            "open": round(row['Open'], 2),
            "high": round(row['High'], 2),
            "low": round(row['Low'], 2),
            "close": round(row['Close'], 2),
            "volume": int(row['Volume']),
            "sma20": round(sma20_hist.iloc[i], 2) if not pd.isna(sma20_hist.iloc[i]) else None,
            "sma50": round(sma50_hist.iloc[i], 2) if not pd.isna(sma50_hist.iloc[i]) else None,
            "sma200": round(sma200_hist.iloc[i], 2) if not pd.isna(sma200_hist.iloc[i]) else None,
            "rsi": round(rsi_hist.iloc[i], 2) if not pd.isna(rsi_hist.iloc[i]) else None,
        })

    return {
        "ticker": ticker,
        "company": quote['company_name'],
        "price": round(current_price, 2),
        "score": round(score, 1),
        "status": final_signal,
        "strategy": strategy,
        "details": details,
        "hc_data": hc_data,
        "vulture_data": vulture_data,
        "alt_data": {
            "score": alt_score,
            "details": alt_details,
            "politician_trades": politician_trades.to_dict('records') if politician_trades is not None else []
        },
        "sentiment": {
            "score": s_score,
            "news_score": news_sentiment
        },
        "chart_data": chart_data,
        "fundamentals": fundamentals,
        "technicals": tech_summary
    }
