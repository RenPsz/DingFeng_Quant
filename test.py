import akshare as ak

print("正在获取沪深300数据...")
df = ak.stock_zh_index_daily(symbol="sh000300")
print(df.head(10))
