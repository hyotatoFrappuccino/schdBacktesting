# yfinance 설치
# pip install yfinance

import yfinance as yf
import pandas as pd

# SCHD 티커로 yfinance 데이터 다운로드
ticker = 'SCHD'
schd = yf.Ticker(ticker)

# 상장일로부터 현재까지 일별 주가 데이터를 가져오기
hist_data = schd.history(period="max")
# 종가, 분배금만 남겨두기
hist_data = hist_data[['Close', 'Dividends']]
# 날짜만 남겨두고 시간 제거
hist_data.index = hist_data.index.date
# 컬렴명을 Close에서 Price로 변경
hist_data.rename(columns={'Close': 'Price'}, inplace=True)
# 수량 열 추가 및 초기값 1로 설정
hist_data['Quantity'] = 1
hist_data.index = pd.to_datetime(hist_data.index)

''' ========== 대출 추적 ========== '''
# """
initial_investment = 7_700_000  # 초기 투자 금액
interest_rate = 0.056  # 대출 금리
exchange_rate = 1163  # 환율
monthly_interest = initial_investment / exchange_rate * interest_rate / 12  # 월 대출 이자
day_of_interest = 14  # 대출 금리 상환일

# 최저 수익률: 34.11%
investment_start_date = pd.to_datetime('2015-03-23')
investment_end_date = pd.to_datetime('2020-03-23')

# 최대 수익률: 169.52%
# investment_start_date = pd.to_datetime('2016-06-13')
# investment_end_date = pd.to_datetime('2021-05-24')

# 시작일과 종료일로 데이터 슬라이싱
hist_data = hist_data.loc[investment_start_date:investment_end_date]
hist_data['Quantity'] = initial_investment / exchange_rate / hist_data['Price'].iloc[0]  # 환율
for i in range(len(hist_data)):
    price = hist_data['Price'].iloc[i]
    dividend = hist_data['Dividends'].iloc[i]
    quantity = hist_data['Quantity'].iloc[i]

    # 배당금이 있는 경우
    if dividend > 0:
        additional_quantity = (quantity * dividend) / price

        # 경고를 피하기 위해 데이터프레임의 복사본을 명시적으로 만들고 수량에 추가
        hist_data.loc[hist_data.index[i:], 'Quantity'] += additional_quantity

# datetime 형식으로 변환된 데이터에서 'Year'와 'Month'를 추출하여 새로운 컬럼 추가
hist_data['Year'] = hist_data.index.year
hist_data['Month'] = hist_data.index.month

# 각 년도와 월에 대해 이자 납부일 처리
for year in hist_data['Year'].unique():
    for month in hist_data.loc[hist_data['Year'] == year, 'Month'].unique():
        # 해당 년도와 월의 데이터 필터링
        monthly_data = hist_data[(hist_data['Year'] == year) & (hist_data['Month'] == month)]

        # 월에 대출 금리 상환일이 있는지 확인하고, 없으면 가장 가까운 이후의 날짜 선택
        if (monthly_data.index.day == day_of_interest).any():
            interest_payment_date = monthly_data[monthly_data.index.day == day_of_interest].index[0]
        else:
            # 대출 금리 상환일이 없다면 그 이후 가장 가까운 날짜 선택
            interest_payment_date = monthly_data.index[monthly_data.index.day > day_of_interest][0]

        # 해당 날짜의 가격과 수량을 가져와서 이자 납부 처리
        price_on_interest_date = hist_data.loc[interest_payment_date, 'Price']
        quantity_on_interest_date = hist_data.loc[interest_payment_date, 'Quantity']

        # monthly_interest 만큼 이자를 납부하고 수량 차감
        quantity_deduction = monthly_interest / price_on_interest_date
        hist_data.loc[interest_payment_date:, 'Quantity'] -= quantity_deduction

# 불필요한 Year와 Month 컬럼 제거
hist_data.drop(columns=['Year', 'Month'], inplace=True)

print(hist_data)

# 초기 총 금액 계산 (기간 시작일의 가격 * 수량)
initial_total_value = hist_data.loc[investment_start_date, 'Price'] * hist_data.loc[investment_start_date, 'Quantity']

# 마지막 총 금액 계산 (기간 종료일의 가격 * 수량)
final_total_value = hist_data.loc[investment_end_date, 'Price'] * hist_data.loc[investment_end_date, 'Quantity']

# 수익률 계산
return_percentage = ((final_total_value / initial_total_value) - 1) * 100

# 데이터프레임의 시작일과 종료일을 기준으로 연 수익률을 계산
start_date = pd.to_datetime(investment_start_date)
end_date = pd.to_datetime(investment_end_date)
total_years = (end_date - start_date).days / 365.25
annual_return_percentage = (final_total_value / initial_total_value) ** (1 / total_years) - 1
annual_return_percentage *= 100

# 수익률과 연평균 수익률을 포맷팅
def format_currency(value):
    return f"{int(value):,}"

# 원화로 변환
initial_total_value_krw = initial_total_value * exchange_rate
final_total_value_krw = final_total_value * exchange_rate

print(f"초기 총 금액: {format_currency(initial_total_value_krw)} KRW")
print(f"마지막 총 금액: {format_currency(final_total_value_krw)} KRW")
print(f"총 수익률: {return_percentage:.2f}%")
print(f"연평균 수익률: {annual_return_percentage:.2f}%")




# 5년 추적
"""
# 5년(약 252*5 거래일) 기간으로 수익률 계산
rolling_window = 252 * 5

# 저장할 리스트
returns = []
start_dates = []
end_dates = []

# 5년 기간의 각 구간에 대해 수익률을 계산
for i in range(len(hist_data) - rolling_window + 1):
    start_date = hist_data.index[i]
    end_date = hist_data.index[i + rolling_window - 1]

    # 구간의 시작일에서 Quantity를 1로 초기화
    temp_data = hist_data.loc[start_date:end_date].copy()
    temp_data['Quantity'] = 1.0

    # 배당금을 재투자하여 수량을 업데이트하는 로직
    for j in range(len(temp_data)):
        price = temp_data['Price'].iloc[j]
        dividend = temp_data['Dividends'].iloc[j]

        if dividend > 0:
            temp_data['Quantity'].iloc[j:] += dividend / price

    # 구간의 최종 가치 계산
    start_price = temp_data['Price'].iloc[0]
    end_price = temp_data['Price'].iloc[-1]
    final_quantity = temp_data['Quantity'].iloc[-1]
    final_value = end_price * final_quantity
    initial_value = start_price * temp_data['Quantity'].iloc[0]

    # 수익률 계산
    return_ = (final_value / initial_value) - 1
    returns.append(return_)
    start_dates.append(start_date)
    end_dates.append(end_date)

# DataFrame으로 변환
results = pd.DataFrame({
    'Start Date': start_dates,
    'End Date': end_dates,
    'Return': returns
})

# 최대 및 최저 수익률 구간 찾기
max_return = results['Return'].max()
max_return_row = results.loc[results['Return'] == max_return].iloc[0]

min_return = results['Return'].min()
min_return_row = results.loc[results['Return'] == min_return].iloc[0]

print(f"최대 수익률: {max_return:.2%}")
print(f"최대 수익률 구간: {max_return_row['Start Date']} ~ {max_return_row['End Date']}")
print(f"최저 수익률: {min_return:.2%}")
print(f"최저 수익률 구간: {min_return_row['Start Date']} ~ {min_return_row['End Date']}")
"""

# 필요에 따라 CSV 파일로 저장할 수 있습니다.
hist_data.to_csv('schd_daily_prices.csv')
