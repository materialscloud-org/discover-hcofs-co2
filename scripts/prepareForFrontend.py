#!/usr/bin/env python3
"""Rebuild everything the app reads (public/data/) from the original archive
files, with the Python standard library only:

    python3 scripts/prepareForFrontend.py [--verify]

Source: Materials Cloud Archive 10.24435/materialscloud:2020.0029/v1 (record
6yq0e-2be96). raw/ holds three files, downloaded from the archive API when
missing and checked against the archive's md5 sums (--verify checks the files
already there too):

- export_hcofs_co2.aiida: the AiiDA 1.0 export (a zip; data.json is 2 GB, read
  whole, then freed: about 9 GB of peak memory, measured; nothing is extracted). The
  CIFs are read from the zip per job, not held all at once.
- properties_COFs.csv: basic properties of all 66,852 COFs (the detail pages).
- properties_COFs_subset.csv: parasitic energy of 961 COFs, used as a check of
  the AiiDA values only.

public/data/ is deleted and written again; the output is deterministic (sorted
names, no timestamps).

Output (public/data/):

- table.json: what the scatter plot needs, one entry per COF, sorted by name,
  null where a COF has no value:
    {"n": 66852, "names": [...], "columns": {"PE": [...], ...}, "categories": {}}
- details/<xxx>.json.gz, xxx = shard_of(name) in hex, three digits or more
  (SHARDS files), gzipped JSON (the app unpacks it with the browser's
  DecompressionStream):
    {"<name>": {"properties": {"<quantity> [<unit>]": value, ...}, "cif": "<CIF text>", "uuid": "<orig_cif node>"}}
  for all 66,852 COFs; properties holds the plotted values the COF has and its
  basic properties from properties_COFs.csv, keys sorted. uuid is the AiiDA
  node of the COF's CIF (orig_cif): the old app opened its page in Materials
  Cloud Explore (explore/hcofs-co2/details/<uuid>) on a click; the COF page
  links it (the AiiDA icon).
  cif is the CIF text of the export's orig_cif file, unchanged: the bytes of
  the archive, decoded as UTF-8 and stored as text (nothing is parsed or
  rewritten here). The app parses it with matsci-parse (fromCIF) for the viewer,
  and offers it unchanged as the CIF download; XSF, XYZ and VASP are written from
  the parsed structure by matsci-parse, in the browser. tests/ checks the CIFs
  against the original files (tests/fixtures/). Gzipped, the CIFs are about a
  third of their text; they are most of the output.

Decisions (what the old app did, and what is done here):

- The values are those of figure/query.py: the Dict node of each COF's group
  with the extra group_tag (pe_out, ht_geom_out, ht_kh_out2, isot_n2_out,
  isot_co2_out), and the orig_cif CifData of the group for the CIF.
- The COF name is the group label (group_ht_<name> or group_pe_<name>), which
  matches properties_COFs.csv exactly. The CifData label is the name for most
  COFs, but truncated ("_relax" for "_relaxed") for 18: not used as the name.
- Scatter table: every COF, with null for a missing value. As in the old app
  (which dropped the COFs missing a value of the plot, its "malformed
  entries"), the explorer plots the COFs that have x, y and colour: all ~66k
  for the geometric quantities, the ~800 screened ones for the CCS quantities.
- Channels ".0" (the first largest sphere): a COF whose list is empty, or which
  has no Channels, has no value: the quirk "some datasets render nothing".
- Values are rounded to 5 significant digits, not 5 decimals: the Henry
  coefficients are 1e-7 to 1e-2 mol/kg/Pa, and 5 decimals would make them 0.
- The subset CSV's parasitic energy (kJ/kg) agrees with the AiiDA PE (MJ/kg)
  to about 1 %; the check fails beyond 2 %.
- shard_of is FNV-1a (32 bit) over the UTF-8 bytes of the name, modulo SHARDS;
  src/common/data.js has the same function (tests/ compares them on fixed names).
"""

import csv
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import sys
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(APP, "raw")
OUT = os.path.join(APP, "public", "data")

RECORD = "6yq0e-2be96"
API = f"https://archive.materialscloud.org/api/records/{RECORD}/files"
AIIDA = "export_hcofs_co2.aiida"
CSV_ALL = "properties_COFs.csv"
CSV_SUBSET = "properties_COFs_subset.csv"
NEEDED = [AIIDA, CSV_ALL, CSV_SUBSET]

SHARDS = 16384  # = config.js SHARD_COUNT
MAX_FILE_BYTES = 25 * 1024 * 1024  # Cloudflare Pages limit per file
MAX_FILES = 20000  # ... and per deployment
EXPECTED_COFS = 66852
SIGNIFICANT = 5

# The plotted quantities, in the order of src/HcofsExplorer/config.js:
# (column, unit, group tag, path of the value in the Dict's attributes, factor).
QUANTITIES = [
    ("PE", "MJ/kg", "pe_out", ("PE",), 1),
    ("WCg", "kg CO2 / kg", "pe_out", ("WCg",), 1),
    ("WCv", "kg CO2 / m^3", "pe_out", ("WCv",), 1),
    ("Pur", "mol/mol", "pe_out", ("Pur",), 1),
    ("Td", "K", "pe_out", ("Td",), 1),
    ("Pd", "bar", "pe_out", ("Pd",), 1),
    ("henry_coefficient_average_ht", "mol/kg/Pa", "ht_kh_out2", ("henry_coefficient_average",), 1),
    ("henry_coefficient_average_n2", "mol/kg/Pa", "isot_n2_out", ("henry_coefficient_average",), 1),
    ("POAV_Volume_fraction", "cm^3/cm^3", "isot_co2_out", ("POAV_Volume_fraction",), 1),
    ("POAV_cm^3/g", "cm^3/g", "isot_co2_out", ("POAV_cm^3/g",), 1),
    ("Density", "g/cm^3", "ht_geom_out", ("Density",), 1),
    ("AV_Volume_fraction", "cm^3/cm^3", "ht_geom_out", ("AV_Volume_fraction",), 1),
    ("Channels.Largest_included_spheres.0", "Angs", "ht_geom_out", ("Channels", "Largest_included_spheres", 0), 1),
    ("Channels.Largest_free_spheres.0", "Angs", "ht_geom_out", ("Channels", "Largest_free_spheres", 0), 1),
]

# The units the archive gives the values of QUANTITIES (checked, not converted).
UNIT_CHECKS = [
    ("pe_out", "PE_units", "MJ/kg"),
    ("pe_out", "Td_units", "K"),
    ("pe_out", "Pd_units", "bar"),
    ("ht_kh_out2", "henry_coefficient_units", "mol/kg/Pa"),
    ("isot_n2_out", "henry_coefficient_units", "mol/kg/Pa"),
]

GROUP = re.compile(r"group_(ht|pe)_(.+)")
UNIT = re.compile(r"\[(.*?)\]")


def shard_of(name):
    h = 0x811C9DC5
    for byte in name.encode("utf-8"):
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return h % SHARDS


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def archive_checksums():
    with urllib.request.urlopen(API) as response:
        entries = json.load(response)["entries"]
    return {e["key"]: e["checksum"].removeprefix("md5:") for e in entries}


def fetch_raw(verify):
    os.makedirs(RAW, exist_ok=True)
    missing = [f for f in NEEDED if not os.path.exists(os.path.join(RAW, f))]
    to_check = NEEDED if verify else missing
    if not to_check:
        return
    sums = archive_checksums()
    for name in to_check:
        path = os.path.join(RAW, name)
        if name in missing:
            print(f"downloading {name} ...")
            part = path + ".part"
            with urllib.request.urlopen(f"{API}/{name}/content") as response, open(part, "wb") as out:
                while chunk := response.read(1 << 20):
                    out.write(chunk)
            os.replace(part, path)
        if md5_of(path) != sums[name]:
            sys.exit(f"md5 mismatch for raw/{name}: expected {sums[name]}")
        print(f"md5 ok: {name}")


def number(value):
    """value as a float with SIGNIFICANT significant digits; None if not a finite number"""
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return float(f"{x:.{SIGNIFICANT}g}") if math.isfinite(x) else None


def dig(obj, path):
    """the value at path (keys, and indices for lists), None if any step is missing"""
    for key in path:
        if obj is None:
            return None
        if isinstance(key, int):
            obj = obj[key] if isinstance(obj, list) and len(obj) > key else None
        else:
            obj = obj.get(key) if isinstance(obj, dict) else None
    return obj


def read_archive(path):
    """{name: {"values": {column: number or None}, "member": zip path of its CIF}} for every COF of the export"""
    with zipfile.ZipFile(path) as z:
        members = set(z.namelist())
        data = json.loads(z.read("data.json"))
        nodes = data["export_data"]["Node"]
        labels = {g["uuid"]: g["label"] for g in data["export_data"]["Group"].values()}
        attrs, extras = data["node_attributes"], data["node_extras"]
        pk_of = {n["uuid"]: pk for pk, n in nodes.items()}
        assert set(data["groups_uuid"]) == set(labels), "groups and their members differ"
        cofs = {}
        for group, uuids in data["groups_uuid"].items():
            match = GROUP.fullmatch(labels[group])
            assert match, f"unexpected group {labels[group]}"
            name = match.group(2)
            pks = [pk_of[u] for u in uuids]
            cifs = [pk for pk in pks if extras.get(pk, {}).get("group_tag") == "orig_cif"]
            assert len(cifs) == 1 and nodes[cifs[0]]["node_type"].startswith("data.cif."), name
            cif = cifs[0]
            assert name.startswith(nodes[cif]["label"]), (name, nodes[cif]["label"])
            tagged = {}
            for pk in pks:
                tag = extras.get(pk, {}).get("group_tag")
                if tag and nodes[pk]["node_type"].startswith("data.dict."):
                    assert tag not in tagged, (name, tag)
                    tagged[tag] = attrs[pk]
            for tag, key, unit in UNIT_CHECKS:
                if tagged.get(tag, {}).get(key, unit) != unit:
                    sys.exit(f"{name}: {tag}.{key} is {tagged[tag][key]}, not {unit}")
            values = {}
            for column, _, tag, attr_path, factor in QUANTITIES:
                raw = dig(tagged.get(tag), attr_path)
                values[column] = None if raw is None else number(raw * factor)
            uuid = nodes[cif]["uuid"]
            member = f"nodes/{uuid[:2]}/{uuid[2:4]}/{uuid[4:]}/path/{attrs[cif]['filename']}"
            assert member in members, member
            cofs[name] = {"values": values, "member": member, "uuid": uuid}
    assert len(cofs) == EXPECTED_COFS, f"expected {EXPECTED_COFS} COFs, got {len(cofs)}"
    return cofs


def column_key(label):
    """import_db-style key of a CSV header: "[unit]" removed, spaces to "_", the unit kept apart"""
    label = label.strip()
    match = UNIT.search(label)
    if match:
        return UNIT.sub("", label).strip().replace(" ", "_"), match.group(1).strip()
    return label.replace(" ", "_"), None


def read_csv(path):
    """{name: {"key [unit]": value}} of a CSV whose first column is the name; numbers rounded, text kept"""
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f, skipinitialspace=True)
        header = next(reader)
        assert header[0] == "name", header[0]
        keys = []
        for label in header:
            key, unit = column_key(label)
            keys.append(key if unit is None else f"{key} [{unit}]")
        assert len(set(keys)) == len(keys), "duplicate column keys"
        table = {}
        for row in reader:
            props = {}
            for key, text in zip(keys[1:], row[1:]):
                value = number(text)
                props[key] = text if value is None else value
            table[row[0]] = props
    assert len(table) == len(set(table)), "duplicate names"
    return table


def check_subset(cofs, subset):
    """the subset's parasitic energy (kJ/kg) against the AiiDA PE (MJ/kg)"""
    key = "parasitic_energy [kJ/kg]"
    rel = []
    for name, props in subset.items():
        pe = cofs[name]["values"]["PE"] if name in cofs else None
        if pe is not None and key in props:
            rel.append(abs(pe * 1000 - props[key]) / props[key])
    assert len(rel) >= 800 and max(rel) < 0.02, f"PE disagrees: {len(rel)} compared, max {max(rel, default=0):.4f}"
    return len(rel), max(rel)


def build_table(cofs, names):
    columns = {column: [cofs[n]["values"][column] for n in names] for column, *_ in QUANTITIES}
    return {"n": len(names), "names": names, "columns": columns, "categories": {}}


def details_properties(cof, basic):
    """the properties of one COF in details/: the plotted values it has, and its basic properties"""
    props = {f"{column} [{unit}]": cof["values"][column] for column, unit, *_ in QUANTITIES if cof["values"][column] is not None}
    overlap = props.keys() & basic.keys()
    assert not overlap, overlap
    props.update(basic)
    return dict(sorted(props.items()))


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, separators=(",", ":"))


def write_text_gz(path, text):
    # mtime=0 and no file name in the header: the same bytes every run
    with open(path, "wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb", compresslevel=GZIP_LEVEL, mtime=0) as f:
        f.write(text.encode("utf-8"))


def read_json_gz(path):
    with gzip.open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


SHARDS_PER_JOB = 64  # shards per job (about 260 COFs); the jobs run in parallel
GZIP_LEVEL = 6  # level 9: 3x slower for 4% smaller files

def read_cif(archive, member):
    """the CIF text of a member of the AiiDA export; nothing is extracted. One ZipFile is shared by
    the threads (its reads are locked): opening the export costs ~30 s and ~3 GB (3.4M entries)."""
    return archive.read(member).decode("utf-8")


def write_shards(first, names_by_shard, cofs, properties, archive):
    """shards first .. first + SHARDS_PER_JOB - 1, written gzipped; returns {shard: number of entries}"""
    counts = {}
    for i in range(first, min(first + SHARDS_PER_JOB, SHARDS)):
        entries = {
            n: {"properties": properties(n), "cif": read_cif(archive, cofs[n]["member"]), "uuid": cofs[n]["uuid"]}
            for n in names_by_shard[i]
        }
        write_text_gz(os.path.join(OUT, "details", f"{i:03x}.json.gz"), json.dumps(entries, separators=(",", ":")))
        counts[i] = len(entries)
    return counts


UNITS = {column: unit for column, unit, *_ in QUANTITIES}


def self_check(archive, cofs, names, table, counts):
    """from the files as written: every shard there, sizes; a sample of shards read in full and checked against the table and the export"""
    files = [os.path.join(d, f) for d, _, fs in os.walk(OUT) for f in fs]
    sizes = [os.path.getsize(f) for f in files]
    assert len(files) == SHARDS + 1 and len(files) < MAX_FILES, len(files)
    assert max(sizes) < MAX_FILE_BYTES, f"file over 25 MiB: {max(sizes)}"
    assert sum(counts.values()) == EXPECTED_COFS == len(names) == table["n"]
    with open(os.path.join(OUT, "table.json"), encoding="utf-8") as f:
        t = json.load(f)
    assert t["n"] == len(t["names"]) == EXPECTED_COFS
    assert all(len(c) == t["n"] and all(v is None or math.isfinite(v) for v in c) for c in t["columns"].values())
    row = {name: i for i, name in enumerate(t["names"])}
    for i in range(0, SHARDS, 97):
        shard = read_json_gz(os.path.join(OUT, "details", f"{i:03x}.json.gz"))
        assert len(shard) == counts[i], f"shard {i:03x}"
        for name, entry in shard.items():
            assert shard_of(name) == i and "_cell_length_a" in entry["cif"], name
            for column, values in t["columns"].items():
                # a missing value: null in the table, absent from the properties
                assert entry["properties"].get(f"{column} [{UNITS[column]}]") == values[row[name]], (name, column)
            assert entry["cif"] == read_cif(archive, cofs[name]["member"]), f"{name}: CIF differs from the export"
            assert entry["uuid"] == cofs[name]["uuid"], f"{name}: uuid"
    return len(files), sum(sizes)


def main():
    fetch_raw("--verify" in sys.argv)
    cofs = read_archive(os.path.join(RAW, AIIDA))
    print(f"{len(cofs)} COFs with a CIF and a group")
    basic = read_csv(os.path.join(RAW, CSV_ALL))
    subset = read_csv(os.path.join(RAW, CSV_SUBSET))
    assert set(basic) == set(cofs), "names of the export and of properties_COFs.csv differ"
    compared, worst = check_subset(cofs, subset)
    print(f"parasitic energy: {compared} COFs of the subset agree with the export (max {worst:.2%})")

    names = sorted(cofs)
    complete = sum(all(cofs[n]["values"][col] is not None for col, *_ in QUANTITIES) for n in names)
    print(f"{complete} COFs with every plotted value")

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "details"))
    archive = zipfile.ZipFile(os.path.join(RAW, AIIDA))
    table = build_table(cofs, names)
    write_json(os.path.join(OUT, "table.json"), table)

    # sorted by name within a shard: the output does not depend on the export's order
    names_by_shard = [[] for _ in range(SHARDS)]
    for name in names:
        names_by_shard[shard_of(name)].append(name)
    properties = lambda n: details_properties(cofs[n], basic[n])  # noqa: E731
    counts = {}
    # threads: the compression (zlib) runs outside Python's lock
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
        jobs = [pool.submit(write_shards, first, names_by_shard, cofs, properties, archive) for first in range(0, SHARDS, SHARDS_PER_JOB)]
        for job in jobs:
            counts.update(job.result())
            print(f"  details: {len(counts)} of {SHARDS} shards", end="\r", flush=True)
    print()

    count, total_bytes = self_check(archive, cofs, names, table, counts)
    shard_sizes = [os.path.getsize(os.path.join(OUT, "details", f"{i:03x}.json.gz")) for i in range(SHARDS)]
    mib = 1024 * 1024
    print(f"public/data/: {count} files, {total_bytes / mib:.0f} MiB")
    print(f"  table.json: {os.path.getsize(os.path.join(OUT, 'table.json')) / mib:.2f} MiB, {len(names)} COFs")
    print(f"  details/: {SHARDS} shards, {min(shard_sizes) / mib:.2f} to {max(shard_sizes) / mib:.2f} MiB")
    archive.close()


if __name__ == "__main__":
    main()
