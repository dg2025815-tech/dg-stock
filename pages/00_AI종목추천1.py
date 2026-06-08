import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="AI Stock Insight", layout="wide")

# --- AI 분석 엔진 ---
def get_ai_analysis(ticker):
    try:
        # 데이터 가져오기 (최근 1년)
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if df.empty:
            return None
        
        # 최신 yfinance 버전의 MultiIndex 문제 해결
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 기술적 지표 계산
        # 1. 이동평균선
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # 2. RSI (상대강도지수)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # 3. 점수 계산 로직
        last = df.iloc[-1]
        score = 50 # 기본점수
        
        # 추세 분석
        if last['Close'] > last['MA20']: score += 15
        if last['MA20'] > last['MA60']: score += 15
        
        # 과매수/과매도 분석
        if last['RSI'] < 35: score += 20 # 과매도 (매수기회)
        elif last['RSI'] > 70: score -= 15 # 과매수 (위험)
        
        # 거래량 분석
        avg_vol = df['Volume'].tail(20).mean()
        if last['Volume'] > avg_vol * 1.5: score += 10

        # 결과 정리
        if score >= 75: status, color = "🔥 강력 매수 추천", "red"
        elif score >= 60: status, color = "✅ 매수 검토", "green"
        elif score >= 40: status, color = "⚖️ 보유 및 관망", "orange"
        else: status, color = "❄️ 매수 비추천", "blue"
        
        return {
            "ticker": ticker,
            "price": last['Close'],
            "score": min(score, 100),
            "status": status,
            "color": color,
            "df": df
        }
    except Exception as e:
        return None

# --- UI 레이아웃 ---
st.title("🤖 AI 주식 추천 분석 대시보드")
st.markdown("전 세계 주식 데이터를 실시간 분석하여 AI 투자 점수를 산출합니다.")

# 사이드바
st.sidebar.header("🔍 분석 설정")
raw_tickers = st.sidebar.text_input("티커 입력 (쉼표 구분)", "NVDA, TSLA, AAPL, 005930.KS, 000660.KS")
tickers = [t.strip().upper() for t in raw_tickers.split(",")]

if tickers:
    analysis_results = []
    
    # 데이터 분석 실행
    for t in tickers:
        with st.spinner(f'{t} 분석 중...'):
            res = get_ai_analysis(t)
            if res:
                analysis_results.append(res)
    
    if analysis_results:
        # 1. 요약 카드 (상단)
        cols = st.columns(len(analysis_results))
        for i, res in enumerate(analysis_results):
            with cols[i]:
                st.markdown(f"### {res['ticker']}")
                st.markdown(f"**{res['score']}점**")
                st.caption(res['status'])
                st.progress(res['score'] / 100)

        # 2. 추천 순위표
        st.divider()
        st.subheader("🏆 AI 추천 우선순위")
        summary_df = pd.DataFrame([{
            "종목": r['ticker'],
            "AI 점수": r['score'],
            "현재가": f"{r['price']:,.2f}",
            "투자 의견": r['status']
        } for r in sorted(analysis_results, key=lambda x: x['score'], reverse=True)])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # 3. 상세 차트 (탭 방식)
        st.divider()
        st.subheader("📈 상세 기술적 분석")
        tabs = st.tabs([r['ticker'] for r in analysis_results])
        
        for i, tab in enumerate(tabs):
            with tab:
                r = analysis_results[i]
                df_plot = r['df'].tail(120) # 최근 120일
                
                fig = go.Figure()
                # 주가 캔들
                fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="주가", line=dict(color='black', width=2)))
                # 이평선
                fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA20'], name="20일선", line=dict(dash='dot')))
                fig.add_trace(go.Scatter(x=df_plot.index, y=df_plot['MA60'], name="60일선", line=dict(dash='dot')))
                
                fig.update_layout(template="plotly_white", height=400, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("데이터를 가져오지 못했습니다. 티커 형식을 확인해 주세요 (예: AAPL, 005930.KS)")
