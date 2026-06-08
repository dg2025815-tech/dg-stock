import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Global Stock Analyzer", layout="wide")

st.title("📈 한·미 주요 주식 수익률 비교 분석")
st.markdown("yfinance와 Plotly를 활용한 실시간 주가 분석 대시보드입니다.")

# 사이드바 설정
st.sidebar.header("🔍 설정")

# 비교할 주식 선택 (사용자 입력 가능)
default_stocks = ['AAPL', 'TSLA', 'NVDA', '005930.KS', '000660.KS', '035420.KS']
tickers = st.sidebar.multiselect(
    "비교할 종목을 선택하거나 티커를 입력하세요:",
    options=['AAPL', 'MSFT', 'TSLA', 'NVDA', 'GOOGL', '005930.KS', '000660.KS', '035420.KS', '035720.KS'],
    default=default_stocks
)

# 기간 선택
period_options = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365, '3년': 1095}
selected_period = st.sidebar.selectbox("분석 기간", list(period_options.keys()), index=2)
days = period_options[selected_period]

start_date = datetime.now() - timedelta(days=days)
end_date = datetime.now()

# 데이터 로드 함수 (캐싱 처리로 속도 향상)
@st.cache_data
def load_data(ticker_list, start, end):
    data = yf.download(ticker_list, start=start, end=end)['Adj Close']
    return data

if tickers:
    try:
        raw_data = load_data(tickers, start_date, end_date)
        
        if len(tickers) == 1:
            raw_data = raw_data.to_frame()
            raw_data.columns = tickers

        # 1. 누적 수익률 계산 (첫 거래일 기준 % 변화)
        returns_df = (raw_data / raw_data.iloc[0] - 1) * 100

        # 메인 화면 - 수익률 비교 차트
        st.subheader(f"📊 선택 종목 누적 수익률 ({selected_period})")
        
        fig = go.Figure()
        for col in returns_df.columns:
            fig.add_trace(go.Scatter(x=returns_df.index, y=returns_df[col], name=col, mode='lines'))
        
        fig.update_layout(
            hovermode="x unified",
            yaxis_title="수익률 (%)",
            xaxis_title="날짜",
            template="plotly_white",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # 2. 상세 지표 요약 (Table)
        st.divider()
        st.subheader("📋 주요 성과 요약")
        
        summary_data = []
        for col in raw_data.columns:
            current_price = raw_data[col].iloc[-1]
            total_return = returns_df[col].iloc[-1]
            volatility = raw_data[col].pct_change().std() * (252**0.5) * 100 # 연율화 변동성
            
            summary_data.append({
                "종목": col,
                "현재가": f"{current_price:,.2f}",
                "누적 수익률": f"{total_return:.2f}%",
                "연 변동성": f"{volatility:.2f}%"
            })
        
        st.table(pd.DataFrame(summary_data))

    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
else:
    st.info("왼쪽 사이드바에서 분석할 종목을 선택해 주세요.")

st.caption("Tip: 한국 주식은 삼성전자(005930.KS), 카카오(035720.KS)와 같이 티커 뒤에 .KS를 붙여주세요.")
