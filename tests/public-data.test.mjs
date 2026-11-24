// The shape of public/data/ (made by scripts/prepareForFrontend.py).
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";
import { fromCIF } from "matsci-parse";

import { config } from "../src/HcofsExplorer/config.js";
import { shardFile, shardOf } from "../src/common/data.js";

const DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "public", "data");
const skip = !fs.existsSync(path.join(DIR, "table.json")) && "run python3 scripts/prepareForFrontend.py first";
const MAX = 25 * 1024 * 1024;
const ROWS = 66852;
const FIXTURES = path.join(path.dirname(fileURLToPath(import.meta.url)), "fixtures");

const read = (file) => {
  const bytes = fs.readFileSync(path.join(DIR, file));
  return JSON.parse((file.endsWith(".gz") ? zlib.gunzipSync(bytes) : bytes).toString("utf8"));
};

test("files: one table, SHARD_COUNT shards, all under 25 MiB, fewer than 20000", { skip }, () => {
  const details = fs.readdirSync(path.join(DIR, "details")).sort();
  assert.equal(details.length, config.shardCount);
  assert.deepEqual(details, Array.from({ length: config.shardCount }, (_, i) => `${i.toString(16).padStart(3, "0")}.json.gz`).sort());
  const files = [...details.map((f) => `details/${f}`), "table.json"];
  assert.deepEqual(fs.readdirSync(DIR).sort(), ["details", "table.json"]);
  assert.ok(files.length < 20000);
  for (const f of files) assert.ok(fs.statSync(path.join(DIR, f)).size < MAX, f);
});

test("table.json: every config column, one value per COF, null where a COF has no value", { skip }, () => {
  const table = read("table.json");
  assert.equal(table.n, ROWS);
  assert.equal(table.names.length, ROWS);
  assert.equal(new Set(table.names).size, ROWS);
  for (const q of config.columns) {
    assert.equal(q.type, "float", q.column);
    const values = table.columns[q.column];
    assert.equal(values.length, ROWS, q.column);
    assert.ok(values.every((v) => v === null || Number.isFinite(v)), q.column);
  }
  assert.deepEqual(Object.keys(table.columns).sort(), config.columns.map((q) => q.column).sort());
  assert.deepEqual(table.categories, {});
});

test("details: the shard of a name holds it, with its properties and its CIF; the table agrees", { skip }, () => {
  const table = read("table.json");
  // the first, the middle and the last of the table, and a COF of another shard
  const last = table.n - 1;
  const sample = [0, Math.floor(last / 2), last].map((i) => table.names[i]);
  for (const name of sample) {
    const shard = read(shardFile(name, config.shardCount));
    const entry = shard[name];
    assert.ok(entry, name);
    assert.deepEqual(Object.keys(entry).sort(), ["cif", "properties", "uuid"]);
    assert.match(entry.uuid, /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/); // the CIF node's AiiDA uuid
    assert.ok(Object.keys(shard).every((n) => shardOf(n, config.shardCount) === shardOf(name, config.shardCount)));
    assert.match(entry.cif, /_cell_length_a/);
    const row = table.names.indexOf(name);
    for (const q of config.columns) {
      // a missing value: null in the table, absent from the properties
      assert.equal(entry.properties[`${q.column} [${q.unit}]`] ?? null, table.columns[q.column][row], `${name} ${q.column}`);
    }
  }
});

test("details: a COF without a plotted value has its CIF and the properties it has", { skip }, () => {
  const table = read("table.json");
  const row = table.columns.PE.indexOf(null);
  assert.ok(row >= 0);
  const name = table.names[row];
  const entry = read(shardFile(name, config.shardCount))[name];
  assert.match(entry.cif, /_cell_length_a/);
  assert.ok(!Object.hasOwn(entry.properties, "PE [MJ/kg]"));
});

test("details: the CIFs are the export's files, unchanged, and matsci-parse reads them", { skip }, () => {
  const fixtures = fs.readdirSync(FIXTURES).filter((f) => f.endsWith(".cif"));
  assert.equal(fixtures.length, 3);
  for (const file of fixtures) {
    const name = file.slice(0, -".cif".length);
    const entry = read(shardFile(name, config.shardCount))[name];
    assert.equal(entry.cif, fs.readFileSync(path.join(FIXTURES, file), "utf8"), name);
    assert.ok(fromCIF(entry.cif).sites.length > 0, name);
  }
});
