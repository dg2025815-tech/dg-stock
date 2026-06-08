import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="AI Stock Recommendation Dashboard", layout="wide")

# --- AI 추천 알고리즘 함수 ---
def analyze_stock(ticker):
    try:
        # 최근 1년치 데이터 다운로드
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None

        # 1. 이동평균선 (MA)
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()

        # 2. RSI (상대강도지수)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 3. 볼린저 밴드
        df['StdDev'] = df['Close'].rolling(window=20).std()
        df['Upper'] = df['MA20'] + (df['StdDev'] * 2)
        df['Lower'] = df['MA20'] - (df['StdDev'] * 2)

        # --- 스코어링 로직 (AI 가중치 모델) ---
        last = df.iloc[-1]
        score = 50  # 기본 점수
        
        # 조건 1: RSI (과매도 시 가점, 과매수 시 감점)
        if last['RSI'] < 30: score += 20  # 과매도 (매수 기회)
        elif last['RSI'] > 70: score -= 15 # 과매수 (경계)
        
        # 조건 2: 이동평균선 (정배열 가점)
        if last['Close'] > last['MA20']: score += 15
        if last['MA20'] > last['MA60']: score += 15
        
        # 조건 3: 볼린저 밴드 (하단 터치 시 가점)
        if last['Close'] <= last['Lower']: score += 10

        # 최종 의견
        if score >= 75: advice = "🔥 강력 매수"
        elif score >= 60: advice = "✅ 매수 검토"
        elif score >= 40: advice = "⚖️ 보유/관망"
        else: advice = "❄️ 매도/주의"

        return {
            "ticker": ticker,
            "current_price": last['Close'],
            "score": min(score, 100),
            "advice": advice,
            "rsi": last['RSI'],
            "df": df
        }
    except:
        return None

# --- UI 레이아웃 ---
st.title("🤖 AI 종목 추천 알고리즘 대시보드")
st.markdown(f"**기준일자:** {datetime.now().strftime('%Y-%m-%d')} | 기술적 지표를 기반으로 AI가 점수를 산출합니다.")

# 사이드바 설정
st.sidebar.header("🔍 분석 대상 설정")
default_tickers = "AAPL, TSLA, NVDA, 005930.KS, 000660.KS, 035420.KS"
input_tickers = st.sidebar.text_input("티커 입력 (쉼표 구분)", default_tickers)
tickers = [t.strip().upper() for t in input_tickers.split(",")]

# 데이터 분석 실행
results = []
with st.spinner('AI가 데이터를 분석 중입니다...'):
    for t in tickers:
        res = analyze_stock(t)
        if res: results.append(res)

if results:
    # 1. 종합 순위 섹션
    st.subheader("🏆 AI 추천 종목 순위")
    summary_df = pd.DataFrame([{
        "순위": i+1,
        "종목": r['ticker'],
        "AI 점수": r['score'],
        "투자 의견": r['advice'],
        "현재가": f"{r['current_price']:,.2f}",
        "RSI": f"{r['rsi']:.1f}"
    } for i, r in enumerate(sorted(results, key=lambda x: x['
