from app.backtest import run_backtest

def test_empty_backtest_is_safe():
    result=run_backtest(101-1,60)
    assert result['samples'] >= 0
    assert 'win_rate' in result
