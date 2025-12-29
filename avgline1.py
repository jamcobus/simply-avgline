import tushare as ts
import pandas as pd
import matplotlib.pyplot as plt

import config
ts.set_token(config.token)
pro = ts.pro_api(config.token)

df = pro.daily(ts_code='600693.SH', start_date='20230101', end_date='20251201')
df['trade_date'] = pd.to_datetime(df['trade_date'])
df.set_index('trade_date', inplace=True)
df.sort_index(inplace=True)  #日期正序排列
#双均线
df.loc[:, 'MA5'] = 0
df.loc[:, 'MA20'] = 0
df['MA5'] = df['close'].rolling(window=5).mean()   
df['MA20'] = df['close'].rolling(window=20).mean() 
df.fillna(0, inplace=True)
print(df['MA20'])

df['Signal'] = 0  # 1代表持有/买入，0代表空仓/卖出
sell = df['MA5']<=df['MA20']
df.loc[df['MA5'] > df['MA20'], 'Signal'] = 1
df['Position'] = df['Signal'].diff()

#忽略滑点
initial_capital = 100000.0 
cash = initial_capital      
hold_shares = 0             
#每日记录
df['Cash'] = initial_capital
df['Hold_Shares'] = 0
df['Total_Asset'] = initial_capital  
buy_signals = 0 
sell_signals = 0
for i in range(1, len(df)):
    current_price = df['close'].iloc[i]
    
    #死叉且有持仓
    if df['Position'].iloc[i] == -1 and hold_shares > 0:
        cash = hold_shares * current_price * 100
        hold_shares = 0
        sell_signals += 1
    
    #金叉且无持仓（可改为有现金时）
    elif df['Position'].iloc[i] == 1 and cash > 0:
        hold_shares = int((cash-10) // (current_price * 100 * 1.0002))
        cash = 0
        buy_signals +=1
    buy_signals=buy_signals
    sell_signals=sell_signals
    
    
    # === 每日更新资产情况 ===
    stock_value = hold_shares * current_price*100  
    total_asset = cash + stock_value           
    
    df.at[df.index[i], 'Cash'] = cash
    df.at[df.index[i], 'Hold_Shares'] = hold_shares
    df.at[df.index[i], 'Total_Asset'] = total_asset

#总资产和收益率
final_total_asset = df['Total_Asset'].iloc[-1]
total_return = (final_total_asset - initial_capital) / initial_capital * 100

print(f"回测结果摘要:")
print(f"初始资金: {initial_capital:.2f} 元")
print(f"最终总资产: {final_total_asset:.2f} 元")
print(f"总收益率: {total_return:.2f}%")
print(f"交易次数 (买入): {int(buy_signals)} 次")
print(f"交易次数 (卖出): {int(sell_signals)} 次")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)

# 均线
ax1.plot(df.index, df['close'], label='收盘价', color='black', alpha=0.7, linewidth=1)
ax1.plot(df.index, df['MA5'], label='MA5', color='red', linewidth=1.5)
ax1.plot(df.index, df['MA20'], label='MA20', color='blue', linewidth=1.5)
#标记买点
buy_signals = df[df['Position'] == 1]
sell_signals = df[df['Position'] == -1]
ax1.scatter(buy_signals.index, buy_signals['close'], color='green', marker='^', s=100, label='买入')
ax1.scatter(sell_signals.index, sell_signals['close'], color='red', marker='v', s=100, label='卖出')
ax1.set_ylabel('价格 (元)')
ax1.set_title('双均线策略 - 价格走势与交易信号')
ax1.legend()
ax1.grid(True)

#资金曲线
ax2.plot(df.index, df['Total_Asset'], label='策略资金曲线', color='purple', linewidth=2)
ax2.fill_between(df.index, cash, df['Total_Asset'], where=(df['Total_Asset'] >= cash), color='lightgreen', alpha=0.5, interpolate=True)
ax2.fill_between(df.index, cash, df['Total_Asset'], where=(df['Total_Asset'] < cash), color='lightcoral', alpha=0.5, interpolate=True)
ax2.axhline(y=cash, color='gray', linestyle='--', linewidth=1, label='初始资金')
ax2.set_xlabel('日期')
ax2.set_ylabel('资金 (元)')
ax2.set_title('策略资金曲线')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()