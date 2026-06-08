import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="Global Stock Analyzer", layout="wide")

st.title("📈 한·미 주요 주식 수익률 비교 분석")

# 사이드바 설정
st.sidebar.header("🔍 설정")

# 기본 선택 종목
default_stocks = ['AAPL', 'TSLA', '005930.KS']
ticker_input = st.sidebar.text_input("티커 직접 입력 (쉼표로 구분):", value="AAPL, TSLA, 005930.KS")
tickers = [t.strip().upper() for t in ticker_input.split(",")]

# 기간 선택
period_options = {'1개월': 30, '3개월': 90, '6개월': 180, '1년': 365, '3년': 1095}
selected_period = st.sidebar.selectbox("분석 기간", list(period_options.keys()), index=2)
days = period_options[selected_period]

start_date = datetime.now() - timedelta(days=days)
end_date = datetime.now()

# 데이터 로드 함수
@st.cache_data
def load_data(ticker_list, start, end):
    try:
        # group_by='column'을 명시하여 데이터 구조 고정
        df = yf.download(ticker_list, start=start, end=end, progress=False)
        if 'Adj Close' in df:
            return df['Adj Close']
        return df['Close']
    except Exception as e:
        st.error(f"데이터 로드 중 오류: {e}")
        return None

if tickers:
    data = load_data(tickers, start_date, end_date)
    
    if data is not None and not data.empty:
        # 데이터가 1개일 경우 Series를 DataFrame으로 변환
        if isinstance(data, pd.Series):
            data = data.to_frame()
            data.columns = tickers

        # 결측치 제거
        data = data.dropna()

        if not data.empty:
            # 1. 누적 수익률 계산
            returns_df = (data / data.iloc[0] - 1) * 100

            # 차트 그리기
            st.subheader(f"📊 선택 종목 누적 수익률 ({selected_period})")
            fig = go.Figure()
            for col in returns_df.columns:
                fig.add_trace(go.Scatter(x=returns_df.index, y=returns_df[col], name=col))
            
            fig.update_layout(hovermode="x unified", yaxis_title="수익률 (%)", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            # 2. 상세 지표 요약
            st.divider()
            st.subheader("📋 주요 성과 요약")
            
            summary_list = []
            for col in data.columns:
                current_price = data[col].iloc[-1]
                total_return = (data[col].iloc[-1] / data[col].iloc[0] - 1) * 100
                summary_list.append({
                    "종목": col,
                    "현재가": round(current_price, 2),
                    "수익률": f"{total_return:.2f}%"
                })
            st.table(pd.DataFrame(summary_list))
        else:
            st.warning("선택한 기간에 대한 데이터가 충분하지 않습니다.")
    else:
        st.error("데이터를 불러오지 못했습니다. 티커가 정확한지 확인해 주세요.")
