from __future__ import annotations
import httpx

WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"

async def get_wikipedia_summary(title: str, lang: str = "en") -> str | None:
    url = WIKI_SUMMARY.format(title.replace(" ", "%20"))
    headers = {"accept-language": lang}
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return data.get("extract")
        return None
