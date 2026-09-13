import httpx

from data_platform.ingestion.usgs import USGS_FEED_URL, fetch_usgs_payload


def test_fetch_usgs_payload_returns_raw_response() -> None:
    expected = b'{"type":"FeatureCollection","features":[]}'

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == USGS_FEED_URL
        return httpx.Response(200, content=expected)

    transport = httpx.MockTransport(handler)

    with httpx.Client(transport=transport) as client:
        result = fetch_usgs_payload(client)

    assert result == expected
