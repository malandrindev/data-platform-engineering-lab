from data_platform.common.health import platform_health


def test_platform_health() -> None:
    result = platform_health()

    assert result["status"] == "ok"
    assert result["service"] == "data-platform-engineering-lab"
