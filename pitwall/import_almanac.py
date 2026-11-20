"""Rebuild the bilingual catalogue from the attributed TracingInsights release."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
# Both archives describe F1DB v2026.20.0 through the 2026 São Paulo GP.
RECORD_SHA = "9ec5ae051b3f0ea97beb345e9ed770097bb2d86c30991da3a6e4ab85c4edc925"
RACES_SHA = "0760d50ecb9fad9f267e14ceece73891c2095c812a71d024d0cfbda1f02b3863"
# Only attach single-event observations to past races. Career totals belong to
# the dated catalogue, even when their context mentions an event.
EVENT_FILES = set("""
fastest-laps/biggest-margin misc/grand-slam-youngest misc/position-gain misc/youngest-hat-trick
misc/youngest-front-row misc/debut-grid misc/debut-result penalties/largest-grid-penalty
penalties/largest-time-penalty pit-stops/winner-most-stops pit-stops/race-most-stops
podiums/youngest-average-age podiums/oldest-average-age poles/largest-margin poles/smallest-margin
races/lap-one-gain races/lap-one-loss races/lap-one-changes races/most-safety-cars
races/most-safety-car-laps races/most-virtual-safety-cars races/most-red-flags sprints/wins-from-grid
seasons/longest-trip
grands-prix/distance-least grands-prix/distance-most
grands-prix/finished-least grands-prix/finished-most grands-prix/time-least grands-prix/time-most
grands-prix/average-least grands-prix/average-most grands-prix/gap-least grands-prix/gap-most
grands-prix/nations-least grands-prix/nations-most
""".split())

SINGLE_OCCURRENCE = {"wins/on-birthday", "poles/on-birthday", "podiums/on-birthday", "poles/did-not-start"}

def verified(path, checksum):
    if hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError(f"Unexpected version of {path.name}. Review coverage and attribution before updating.")
    return ZipFile(path)


def rows(archive, filename):
    with archive.open(filename) as stream:
        return list(csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    parser.add_argument("f1db", type=Path)
    args = parser.parse_args()
    with verified(args.f1db, RACES_SHA) as source:
        calendar = {r["officialName"]: f"{r['year']}-{r['round']}" for r in rows(source,"f1db-races.csv")}
    topics = []
    with verified(args.records, RECORD_SHA) as source:
        index = {r["file"]: r for r in rows(source,"index.csv")}
        for line in (HERE/"record-topics.tsv").read_text(encoding="utf8").splitlines():
            filename, zh = line.split("\t")
            meta = index[filename]
            key = filename.removesuffix(".csv")
            if meta["licence"] != "CC BY 4.0":
                raise ValueError(f"Unexpected licence for {key}")
            entries = rows(source,filename)[:10]
            for entry in entries:
                single = key in SINGLE_OCCURRENCE and entry["value"] == "1"
                if key in EVENT_FILES or single:
                    context = re.sub(r" \(age \d+\)$", "", entry["context"]) if single else entry["context"]
                    gp = calendar.get(context) or calendar.get(entry["name"])
                    if gp:
                        entry["gp"] = gp
            topics.append(dict(key=key,zh=zh,en=meta["title"],unit=meta["value_label"],
                               context=meta["context_label"],definition=meta["methodology"],
                               coverage=meta["coverage"],total=int(meta["rows"]),entries=entries))
    if len(topics) != len({t["key"] for t in topics}):
        raise ValueError("Duplicate topic")
    content = "window.PITWALL_BOOK=" + json.dumps(topics,ensure_ascii=False,separators=(",",":")) + ";\n"
    dest = HERE/"dist/almanac-data.js"
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(content,encoding="utf8")
    tmp.replace(dest)
    linked = [e["gp"] for t in topics for e in t["entries"] if "gp" in e]
    print(f"{len(topics)} topics, {sum(len(t['entries']) for t in topics)} examples, "
          f"{len(linked)} linked observations in {len(set(linked))} GPs")


if __name__ == "__main__":
    main()
