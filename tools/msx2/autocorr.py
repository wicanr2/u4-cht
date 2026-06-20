import sys
data=open(sys.argv[1],"rb").read()
n=len(data)
# 對「位元組是否相等於 lag 後位元組」的比例做自相關,找週期
print(f"size={n}")
res=[]
for lag in range(1,260):
    same=sum(1 for i in range(n-lag) if data[i]==data[i+lag])
    res.append((same/(n-lag),lag))
# 列出相關性最高的 lag(排除非常小的)
res.sort(reverse=True)
print("top lags by byte-equality autocorrelation:")
for sc,lag in res[:15]:
    print(f"  lag={lag:4d}  score={sc:.3f}")
