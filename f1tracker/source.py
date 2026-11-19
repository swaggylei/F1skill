"""Jolpica/Ergast GP-only adapter. Secondary evidence always remains provisional."""
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import __version__
from .model import DataError, digest, require, utcnow
from .store import atomic_write

BASE = "https://api.jolpi.ca/ergast/f1"
NON_STARTERS = {"Did not start", "Did not qualify", "Did not prequalify", "Withdrawn", "107% Rule"}


class Client:
    def __init__(self, cache_directory, opener=None, sleep=time.sleep):
        self.cache = Path(cache_directory)
        self.opener = opener or urllib.request.urlopen
        self.sleep = sleep

    def get(self, url):
        # Cache is an audit archive, never a stale fallback for a failed discovery.
        for attempt in range(3):
            self.sleep(0.3)
            try:
                request = urllib.request.Request(url, headers={"User-Agent": f"F1KnowledgeTracker/{__version__}", "Accept": "application/json"})
                with self.opener(request, timeout=25) as response:
                    if hasattr(response, "geturl") and not response.geturl().startswith("https://"):
                        raise DataError("Refusing an HTTPS downgrade")
                    raw = response.read(5_000_001)
                    require(len(raw) <= 5_000_000, "Source response exceeds size limit")
                    data = json.loads(raw)
                    atomic_write(self.cache / (digest(data) + ".json"), json.dumps(data, ensure_ascii=False, indent=2) + "\n")
                    return data
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise DataError(f"Source HTTP {exc.code}: {url}") from exc
                retry = exc.headers.get("Retry-After", "") if exc.headers else ""
                delay = max(2 ** attempt, int(retry) if retry.isdigit() else 0)
                if delay > 60:
                    raise DataError(f"Source requests a {delay}s cooldown; retry on the next scheduled run") from exc
                self.sleep(delay)
            except (urllib.error.URLError, TimeoutError) as exc:
                if "403" in str(exc) or attempt == 2:
                    raise DataError(f"Source unavailable: {url}: {exc}") from exc
                self.sleep(2 ** attempt)
        raise DataError("Source unavailable")


def pages(client, path, results=False):
    offset, total, races = 0, None, {}
    for _ in range(100):
        url = f"{BASE}/{path}/?limit=100&offset={offset}"
        data = client.get(url)["MRData"]
        require(data["series"] == "f1" and int(data["offset"]) == offset, "Unexpected API series/offset")
        page_total = int(data["total"])
        require(page_total >= 0 and (total is None or page_total == total), "API changed during pagination; retry later")
        total = page_total
        count = 0
        for race in data["RaceTable"]["Races"]:
            key = (race["season"], race["round"])
            count += len(race["Results"]) if results else 1
            if key in races:
                require(results, "Duplicate calendar event")
                require({k: v for k, v in race.items() if k != "Results"} ==
                        {k: v for k, v in races[key].items() if k != "Results"}, "Race metadata changed across pages")
                races[key]["Results"].extend(race["Results"])
            else:
                races[key] = race
        require(offset + count <= total, "Pagination total mismatch")
        offset += count
        if offset == total:
            return races
        require(count > 0, "Truncated/empty API page before total")
    raise DataError("Pagination limit exceeded; no partial results committed")


def normalize(race, retrieved_at):
    season, round_ = int(race["season"]), int(race["round"])
    rows = []
    for result in race["Results"]:
        status = result.get("status")
        require(isinstance(status, str) and status.strip(), "Missing status; cannot infer participation")
        driver, team = result["Driver"], result["Constructor"]
        started = status not in NON_STARTERS
        dsq = status in ("Disqualified", "Excluded")
        finished = status == "Finished" or (status.startswith("+") and "Lap" in status)
        grid = int(result["grid"]) if result.get("grid") else None
        rows.append({"driver_id": driver["driverId"], "driver_name": driver["givenName"] + " " + driver["familyName"],
                     "constructor_id": team["constructorId"], "date_of_birth": driver.get("dateOfBirth"),
                     "position": int(result["position"]) if started and not dsq else None,
                     "grid": grid if grid and grid > 0 else None, "points": result["points"],
                     "started": started, "disqualified": dsq, "finished": finished and started and not dsq})
    return {"event_id": f"{season}-{round_:02d}-gp", "season": season, "round": round_, "session": "gp",
            "name": race["raceName"], "date": race["date"], "completed": True,
            "official_status": "unknown", "verification": "provisional",
            "pending_reviews": ["Secondary API only: verify final FIA result, open decisions and historical comparator"],
            "sources": [{"url": f"{BASE}/{season}/{round_}/results/", "title": race["raceName"] + " GP results",
                         "publisher": "Jolpica-F1", "role": "secondary", "retrieved_at": retrieved_at}], "results": rows}


def sync(client, start_season, end_season, now=None):
    now = now or datetime.now(timezone.utc)
    require(2000 <= start_season <= end_season <= now.year, "Use a bounded season range from 2000 through the current year")
    events, gaps = [], []
    for season in range(start_season, end_season + 1):
        calendar = pages(client, f"{season}/races")
        results = pages(client, f"{season}/results", results=True)
        require(calendar, f"No calendar returned for {season}")
        for key, race in calendar.items():
            require(int(race["season"]) == season, "Calendar returned wrong season")
            scheduled = datetime.fromisoformat(race["date"] + "T" + race.get("time", "00:00:00Z").replace("Z", "+00:00"))
            if key not in results:
                # A late result is unresolved, not proof of completion or cancellation.
                if scheduled + timedelta(hours=8) < now:
                    gaps.append(f'{season} round {race["round"]}: scheduled in past but no GP result; check postponement/cancellation/source lag')
                continue
            result = results.pop(key)
            require(scheduled <= now, "Source returned results for a future event")
            require(all(result[k] == race[k] for k in ("season", "round", "raceName", "date")), "Calendar/result identity mismatch")
            events.append(normalize(result, now.isoformat()))
        require(not results, "Results contain events missing from the calendar")
    require(not gaps, "Coverage incomplete: " + "; ".join(gaps))
    require(events, "No completed GP classification available; no success watermark written")
    return {"schema_version": 1,
            "coverage": {"label": f"GP history since {start_season} (Jolpica, bounded)",
                         "start_season": start_season, "end_season": end_season,
                         "expected_event_ids": [e["event_id"] for e in events]}, "events": events}
