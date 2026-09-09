from app.scoring import score_pair

def base(**kw):
    p={"price_change_1h":0,"price_change_24h":0,"volume_24h":10000,"liquidity":10000,"buys_24h":50,"sells_24h":50}
    p.update(kw); return p

def test_scores_are_bounded():
    opp,risk,parts,_=score_pair(base(price_change_1h=10000,price_change_24h=-10000,liquidity=0))
    assert 0<=opp<=100 and 0<=risk<=100
    assert all(0<=v<=100 for v in parts.values())

def test_buy_pressure_moves_up():
    low=score_pair(base(buys_24h=10,sells_24h=90))[2]["buy_pressure"]
    high=score_pair(base(buys_24h=90,sells_24h=10))[2]["buy_pressure"]
    assert high>low

def test_missing_and_bad_values_do_not_crash():
    opp,risk,_,_=score_pair({"price_change_1h":"bad","volume_24h":None,"liquidity":0})
    assert 0<=opp<=100 and 0<=risk<=100
