import httpx

USGS_FEED_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
)


def fetch_usgs_payload(client: httpx.Client, url: str = USGS_FEED_URL) -> bytes:
    response = client.get(url)
    response.raise_for_status()
    return response.content
