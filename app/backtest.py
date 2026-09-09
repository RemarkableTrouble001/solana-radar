from datetime import datetime, timezone
from .db import conn

def _dt(x):
    return datetime.fromisoformat(x.replace('Z','+00:00'))

def run_backtest(threshold=70.0, horizon_minutes=60):
    with conn() as c:
        signals=c.execute("SELECT timestamp,token_address,entry_price,opportunity_score FROM signals WHERE opportunity_score>=? ORDER BY timestamp",(threshold,)).fetchall()
        outcomes=[]
        for s in signals:
            target=_dt(s['timestamp'])
            future=c.execute("SELECT observed_at,price_usd FROM observations WHERE token_address=? AND observed_at>? ORDER BY observed_at",(s['token_address'],s['timestamp'])).fetchall()
            chosen=None
            for row in future:
                if (_dt(row['observed_at'])-target).total_seconds() >= horizon_minutes*60:
                    chosen=row; break
            if chosen and s['entry_price'] and chosen['price_usd']:
                ret=(chosen['price_usd']/s['entry_price']-1)*100
                outcomes.append(ret)
        if not outcomes:
            return {"threshold":threshold,"horizon_minutes":horizon_minutes,"samples":0,"win_rate":None,"avg_return_pct":None,"median_return_pct":None}
        ordered=sorted(outcomes); mid=len(ordered)//2
        median=ordered[mid] if len(ordered)%2 else (ordered[mid-1]+ordered[mid])/2
        return {"threshold":threshold,"horizon_minutes":horizon_minutes,"samples":len(outcomes),"win_rate":round(sum(x>0 for x in outcomes)/len(outcomes)*100,2),"avg_return_pct":round(sum(outcomes)/len(outcomes),2),"median_return_pct":round(median,2)}
