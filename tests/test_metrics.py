from collections import Counter

from app import metrics
from app.metrics import percentile


def test_percentile_basic() -> None:
    assert percentile([100, 200, 300, 400], 50) >= 100


def test_error_rate_uses_all_attempts(monkeypatch) -> None:
    monkeypatch.setattr(metrics, "TRAFFIC", 1)
    monkeypatch.setattr(metrics, "ERRORS", Counter({"TimeoutError": 1}))

    result = metrics.snapshot()

    assert result["traffic"] == 2
    assert result["error_rate_pct"] == 50.0
