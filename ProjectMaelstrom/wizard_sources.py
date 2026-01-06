import requests, json, datetime
from urllib.parse import urlparse

sources = [
    ("Wizard101 Wiki (Fandom)", "https://wizard101.fandom.com/"),
    ("Wizard101 Official", "https://www.wizard101.com/"),
    ("KingsIsle", "https://www.kingsisle.com/"),
    ("Wizard101 Central", "https://www.wizard101central.com/"),
    ("Reddit r/Wizard101", "https://www.reddit.com/r/Wizard101/"),
    ("Steam Wizard101", "https://store.steampowered.com/app/799960/Wizard101/"),
    ("YouTube", "https://www.youtube.com/results?search_query=Wizard101+quest+walkthrough"),
    ("Twitch", "https://www.twitch.tv/directory/game/Wizard101"),
    ("Public Guides/Blogs", "https://www.google.com/search?q=Wizard101+guide"),
    ("Public Sheets/Repos", "https://github.com/search?q=Wizard101"),
    ("Fan image galleries", "https://wizard101.fandom.com/wiki/Category:Maps"),
    ("YouTube captions", "https://www.youtube.com/results?search_query=Wizard101+walkthrough+subtitles"),
    ("User media", "user_provided"),
    ("Item/Spell DB (wiki)", "https://wizard101.fandom.com/wiki/Category:Items"),
    ("Public tooling repos", "https://github.com/search?q=Wizard101+tool"),
]

keywords_list = ["quest", "npc", "map", "item", "spell", "walkthrough", "transcript", "caption"]

session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0 (repo-eval)"}


def check_robots(url):
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        r = session.get(base + "/robots.txt", headers=headers, timeout=8)
        if r.status_code != 200:
            return "unknown", None
        txt = r.text.lower()
        if "disallow: /" in txt and "allow: /" not in txt:
            return "no", txt[:500]
        return "yes", txt[:500]
    except Exception:
        return "unknown", None


def build_entry(name, url):
    entry = {
        "source_name": name,
        "url": url,
        "reachable": True,
        "scrape_allowed": "unknown",
        "best_extraction_method": "HTML_scrape",
        "data_types_available": [],
        "sample_metadata": None,
        "license_copyright_notes": "",
        "estimated_collection_feasibility": "medium",
        "suggested_next_steps": [],
        "notes": ""
    }
    if url == "user_provided":
        entry.update({
            "reachable": True,
            "scrape_allowed": "yes",
            "best_extraction_method": "user_media_only",
            "data_types_available": ["screenshots", "walkthrough_steps", "map_images"],
            "sample_metadata": "Awaiting user-provided recordings/screenshots",
            "license_copyright_notes": "Use only media provided with permission; keep local.",
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Ingest provided screenshots and annotate objectives"],
        })
        return entry

    try:
        r = session.head(url, headers=headers, allow_redirects=True, timeout=10)
        entry["reachable"] = r.status_code < 400
    except Exception as e:
        entry["reachable"] = False
        entry["notes"] = str(e)

    robots_flag, robots_sample = check_robots(url)
    entry["scrape_allowed"] = robots_flag

    lower = url.lower()
    if "fandom" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["quest_text", "objectives", "npc_locations", "map_images", "item_tables", "spell_tables", "walkthrough_steps", "screenshots"],
            "sample_metadata": "Example quest page: https://wizard101.fandom.com/wiki/Quest:Find_Lost_Scrolls",
            "license_copyright_notes": "User-contributed; follow Fandom TOS; attribute." ,
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Respect robots; rate limit 1 req/sec; extract infoboxes and quest sections with provenance"]
        })
    elif "wizard101.com" in lower or "kingsisle" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["patch_notes", "walkthrough_steps", "screenshots"],
            "sample_metadata": "Example patch notes: https://www.wizard101.com/game/updates",
            "license_copyright_notes": "Official content; copyrighted; use summaries/metadata with attribution.",
            "estimated_collection_feasibility": "medium",
            "suggested_next_steps": ["Collect patch note titles/dates; do not copy full text"]
        })
    elif "wizard101central" in lower:
        entry.update({
            "best_extraction_method": "manual_copy",
            "data_types_available": ["walkthrough_steps", "map_images", "item_tables", "spell_tables", "community_comments"],
            "sample_metadata": "Example guide: https://www.wizard101central.com/wiki/Quest:Main_Story_Quests",
            "license_copyright_notes": "Fan site; check site terms; manual excerpts with attribution.",
            "estimated_collection_feasibility": "medium",
            "suggested_next_steps": ["Manual curation of key quest guides with links"]
        })
    elif "reddit.com" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["community_comments", "walkthrough_steps", "screenshots"],
            "sample_metadata": "Example thread: https://www.reddit.com/r/Wizard101/",
            "license_copyright_notes": "User content; Reddit terms; quote minimally with links.",
            "estimated_collection_feasibility": "medium",
            "suggested_next_steps": ["Collect post titles/links via RSS/JSON; avoid full comments storage"]
        })
    elif "store.steampowered.com" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["community_comments", "screenshots", "patch_notes"],
            "sample_metadata": "Discussions: https://steamcommunity.com/app/799960/discussions/",
            "license_copyright_notes": "Valve/Steam content; use metadata only.",
            "estimated_collection_feasibility": "medium",
            "suggested_next_steps": ["Grab announcement titles/dates; link to discussions"]
        })
    elif "youtube.com" in lower:
        entry.update({
            "best_extraction_method": "YouTube_API",
            "data_types_available": ["walkthrough_steps", "video_transcripts", "timestamps", "screenshots"],
            "sample_metadata": "Query: Wizard101 quest walkthrough",
            "license_copyright_notes": "Videos copyrighted; captions via API; request permission for reuse.",
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Use YouTube Data API to list videos and fetch captions where available"]
        })
    elif "twitch.tv" in lower:
        entry.update({
            "best_extraction_method": "manual_copy",
            "data_types_available": ["walkthrough_steps", "video_transcripts", "timestamps"],
            "sample_metadata": "Twitch directory for Wizard101",
            "license_copyright_notes": "VODs copyrighted; need permission; metadata only.",
            "estimated_collection_feasibility": "low",
            "suggested_next_steps": ["Collect VOD titles/dates manually with creator permission"]
        })
    elif "google.com" in lower:
        entry.update({
            "best_extraction_method": "manual_copy",
            "data_types_available": ["walkthrough_steps", "screenshots", "map_images"],
            "sample_metadata": "Search results for Wizard101 guide",
            "license_copyright_notes": "Various sites; check each site's terms before use.",
            "estimated_collection_feasibility": "medium",
            "suggested_next_steps": ["Curate a shortlist of public guides with attribution"]
        })
    elif "github.com/search?q=wizard101+tool" in lower or "github.com/search?q=wizard101" in lower:
        entry.update({
            "best_extraction_method": "github_search",
            "data_types_available": ["item_tables", "spell_tables", "walkthrough_steps", "map_images"],
            "sample_metadata": "Search GitHub for Wizard101 data/scripts",
            "license_copyright_notes": "Respect repo licenses (MIT/Apache/etc.).",
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Collect repo metadata and LICENSE for any datasets"]
        })
    elif "category:maps" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["map_images", "screenshots"],
            "sample_metadata": "Fandom map category page",
            "license_copyright_notes": "User-contributed images; attribution per Fandom TOS.",
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Download map thumbnails with attribution; store provenance"]
        })
    elif "items" in lower:
        entry.update({
            "best_extraction_method": "HTML_scrape",
            "data_types_available": ["item_tables", "spell_tables", "screenshots"],
            "sample_metadata": "Fandom items category",
            "license_copyright_notes": "User-contributed; attribute per Fandom TOS.",
            "estimated_collection_feasibility": "high",
            "suggested_next_steps": ["Extract item/spell infoboxes with provenance"]
        })
    else:
        entry["best_extraction_method"] = "HTML_scrape"
    return entry

entries = [build_entry(n, u) for n, u in sources]
summary_recommended = [e["url"] for e in entries if e.get("estimated_collection_feasibility") in ("high", "medium") and e.get("reachable", True)]
quick_actions = [
    "Rate-limit wiki HTML parsing (1 req/sec) and extract quest/infobox fields with provenance",
    "Use YouTube Data API to fetch video metadata/captions for 'Wizard101 quest walkthrough' queries",
    "Collect public map thumbnails from wiki categories with attribution",
    "Curate GitHub/Wiki item/spell tables with LICENSE provenance",
    "Manually curate key guides from Wizard101 Central/official patch notes with links"
]

report = {
    "project": "Wizard101-quest-data-sources",
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
    "sources": entries,
    "summary": {
        "recommended_sources_for_initial_collection": summary_recommended[:7],
        "quick_actions": quick_actions,
        "legal_and_ethics_notes": "Use only public/read-only content; respect robots.txt and site terms; attribute sources; do not extract from client/servers or private communities."
    }
}

with open("wizard101_data_sources.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
