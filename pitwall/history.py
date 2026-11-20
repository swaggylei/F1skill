"""Build the offline championship archive from a checksummed F1DB CSV release."""
import argparse
import csv
from collections import defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
from zipfile import ZipFile

API = "https://api.github.com/repos/f1db/f1db/releases/latest"
OUT = Path(__file__).parent / "dist/archive-data.js"


def download(url, accept):
    request = Request(url, headers={"User-Agent": "Pitwall-history", "Accept": accept})
    with urlopen(request, timeout=120) as response:
        return response.read()


def export(raw, tag, checksum, cutoff):
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError("F1DB archive checksum mismatch")
    if not re.fullmatch(r"v\d{4}\.\d+\.\d+", tag):
        raise ValueError("Expected a stable F1DB release tag")
    with ZipFile(io.BytesIO(raw)) as archive:
        def read(table):
            with archive.open(f"f1db-{table}.csv") as stream:
                return list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig")))
        def lookup(table, field):
            return {row["id"]: row[field] for row in read(table)}
        drivers = lookup("drivers", "name")
        teams = lookup("constructors", "name")
        names = lookup("grands-prix", "fullName")
        circuits = lookup("circuits", "fullName")
        results = defaultdict(list)
        qualifying = defaultdict(list)
        for row in read("races-qualifying-results"):
            qualifying[row["raceId"]].append(row)
        for r in sorted(read("races-race-results"), key=lambda row: int(row["positionDisplayOrder"])):
            results[r["raceId"]].append([r["positionText"], drivers[r["driverId"]], teams[r["constructorId"]],
                                         r["gridPositionText"], r["laps"], r["points"], r["sharedCar"] == "true",
                                         r["reasonRetired"], r["driverId"]])
        races = []
        for r in sorted(read("races"), key=lambda row: (int(row["year"]), int(row["round"]))):
            if r["date"] > cutoff.isoformat():
                continue
            rows = results.get(r["id"], [])
            if not rows or not any(row[0] == "1" for row in rows):
                raise ValueError(f"Missing classification for {r['officialName']}")
            race = dict(year=int(r["year"]), round=int(r["round"]), date=r["date"],
                        name=names[r["grandPrixId"]], circuit=circuits[r["circuitId"]], rows=rows)
            # Known standard GP knockout formats only. Sprint qualifying is a separate file.
            year = race["year"]
            if r["qualifyingFormat"] == "KNOCKOUT" and 2017 <= year <= 2026:
                times = qualifying[r["id"]]
                cutoff_places = 16 if year == 2026 else 15
                if any(row["q2Millis"] for row in times):
                    race["q1"] = {}
                    for row in times:
                        if row["q2Millis"] or row["q3Millis"]:
                            race["q1"][row["driverId"]] = "advanced"
                        elif row["q1Millis"] and row["positionText"].isdigit():
                            faster = sum(bool(other["q1Millis"]) and int(other["q1Millis"]) < int(row["q1Millis"])
                                         for other in times)
                            if faster >= cutoff_places:
                                race["q1"][row["driverId"]] = "out"
            races.append(race)
    if not races or races[0]["year"] != 1950:
        raise ValueError("Missing opening season")
    seasons = defaultdict(list)
    for race in races:
        seasons[race["year"]].append(race["round"])
    if list(seasons) != list(range(1950, races[-1]["year"] + 1)) or any(
            rounds != list(range(1, len(rounds) + 1)) for rounds in seasons.values()):
        raise ValueError("Non-contiguous season or round coverage")
    data = dict(release=tag, checksum=checksum, races=races)
    temp = OUT.with_suffix(".tmp")
    temp.write_text("window.PITWALL_HISTORY=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n",
                    encoding="utf8")
    temp.replace(OUT)
    print(f"{len(seasons)} seasons / {len(races)} GPs / {sum(len(r['rows']) for r in races)} result rows")
    print(races[0]["date"], "through", races[-1]["date"], races[-1]["name"])


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--zip", type=Path)
    cli.add_argument("--tag")
    cli.add_argument("--sha256")
    cli.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    args = cli.parse_args()
    if args.zip:
        if not args.tag or not args.sha256:
            cli.error("Local ZIP needs --tag and --sha256 from its release")
        export(args.zip.read_bytes(), args.tag, args.sha256, args.as_of)
    else:
        release = json.loads(download(API, "application/vnd.github+json"))
        asset = next(a for a in release["assets"] if a["name"] == "f1db-csv.zip")
        raw = download(asset["url"] + "?format=zip", "application/octet-stream")
        export(raw, release["tag_name"], asset["digest"].removeprefix("sha256:"), args.as_of)
