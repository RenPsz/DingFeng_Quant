import pytest

import main


@pytest.mark.e2e
def test_main_runs_offline_research_flow(price_data, monkeypatch, capsys):
    monkeypatch.setattr(main.data, "refresh_indices", lambda: None)
    monkeypatch.setattr(main.data, "get_stock_data", lambda symbol: price_data)

    main.main()

    output = capsys.readouterr().out
    assert "最新因子快照" in output
    assert "factor" in output
    assert "momentum_low" in output

