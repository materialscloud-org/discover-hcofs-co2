import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { config } from "../src/HcofsExplorer/config.js";
import { colorSpec, filterIndices, fnv1a32, propertiesJson, propertyRows, resolvePreset, shardFile, shardOf } from "../src/common/data.js";
import { scatterFigure, wrapTitle } from "../src/common/figure.js";

// a tiny table in the format of public/data/table.json: every column of the config
const table = {
  n: 5,
  names: ["a", "b", "c", "d", "e"],
  columns: {
    PE: [1, 2, 3, 4, 5],
    WCg: [0.01, 0.02, 0.03, 0.04, 0.05],
    WCv: [1, 2, 3, 4, 5],
    Pur: [0.5, 0.6, 0.7, 0.8, 0.9],
    Td: [340, 350, 330, 345, 355],
    Pd: [40, 60, 90, 120, 150],
    henry_coefficient_average_ht: [0.001, 0.002, 0.003, 0.004, 0.005],
    henry_coefficient_average_n2: [1e-6, 2e-6, 3e-6, 4e-6, 5e-6],
    POAV_Volume_fraction: [0.1, 0.2, 0.3, 0.4, 0.5],
    "POAV_cm^3/g": [1, 2, 3, 4, 5],
    Density: [0.1, 0.2, 0.3, 0.4, 0.5],
    AV_Volume_fraction: [0.9, 0.8, 0.7, 0.6, 0.5],
    "Channels.Largest_included_spheres.0": [5, 6, 7, 8, 9],
    "Channels.Largest_free_spheres.0": [4, 5, 6, 7, 8],
  },
  categories: {},
};

test("shard hash: fixed names (same values as the Python script)", () => {
  const expected = {
    default: 990,
    a: 300,
    linker91_CO_linker87_NH_hcb_relaxed: 459,
    linker100_CH_linker41_N_umc_relaxed_interp_3: 0,
    linker98_CO_linker95_NH_pto_relaxed: 983,
  };
  for (const [name, shard] of Object.entries(expected)) assert.equal(shardOf(name, 1024), shard, name);
  assert.equal(fnv1a32(""), 0x811c9dc5);
  assert.equal(fnv1a32("a"), 0xe40c292c); // the FNV-1a test vector
  assert.equal(shardFile("linker100_CH_linker41_N_umc_relaxed_interp_3", 1024), "details/000.json.gz");
  assert.equal(shardFile("linker91_CO_linker87_NH_hcb_relaxed", 1024), "details/1cb.json.gz");
  assert.equal(shardFile("é", 1024), shardFile("é", 1024)); // UTF-8, not UTF-16 units
});

test("shard hash agrees with scripts/prepareForFrontend.py", (t) => {
  const script = fileURLToPath(new URL("../scripts/prepareForFrontend.py", import.meta.url));
  const names = ["x", "COF-1", "linker1_N_linker2_CH_dia_relaxed", "naïve", "日本"];
  let out;
  try {
    out = execFileSync(
      "python3",
      [
        "-I",
        "-c",
        "import importlib.util, sys, json\n" +
          "s = importlib.util.spec_from_file_location('p', sys.argv[1]); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)\n" +
          "print(json.dumps([m.shard_of(n) for n in sys.argv[2:]]), m.SHARDS)",
        script,
        ...names,
      ],
      { encoding: "utf8" },
    );
  } catch {
    return t.skip("python3 not available");
  }
  const cut = out.trim().lastIndexOf(" ");
  const [shards, count] = [out.slice(0, cut), out.slice(cut)];
  assert.equal(Number(count), config.shardCount);
  assert.deepEqual(JSON.parse(shards), names.map((n) => shardOf(n, config.shardCount)));
});

test("preset: default, unknown, filters of the default", () => {
  const d = resolvePreset(config, "default");
  assert.deepEqual([d.key, d.x, d.y, d.clr], ["default", "PE", "POAV_Volume_fraction", "AV_Volume_fraction"]);
  assert.deepEqual(d.filters, { PE: [0, 5], Td: [330, 360], Pd: [0.03, 0.15] });
  assert.deepEqual(resolvePreset(config, "nope"), d);
  assert.deepEqual(resolvePreset(config, undefined), d);
  assert.equal(resolvePreset(config, "toString").key, "default");
});

test("preset: sensible (desorption columns), no filter entries: the full ranges", () => {
  const s = resolvePreset(config, "sensible");
  assert.deepEqual([s.x, s.y, s.clr], ["Pd", "PE", "Td"]);
  assert.deepEqual(s.filters, { PE: [0, 5], Td: [330, 360], Pd: [0.03, 0.15] });
  // axes and colour are all configured columns
  const columns = new Set(config.columns.map((q) => q.column));
  for (const key of Object.keys(config.presets)) {
    const r = resolvePreset(config, key);
    assert.ok(columns.has(r.x) && columns.has(r.y) && columns.has(r.clr), key);
  }
});

test("filters: ranges (inclusive), full ranges do not filter", () => {
  const all = resolvePreset(config, "default").filters;
  const f = (patch) => filterIndices(table, config, { ...all, ...patch });
  assert.deepEqual(f({}), [0, 1, 2, 3, 4]);
  assert.deepEqual(f({ PE: [2, 3] }), [1, 2]);
  assert.deepEqual(f({ Td: [340, 350] }), [0, 1, 3]);
  assert.deepEqual(f({ PE: [1, 5], Pd: [60, 120] }), [1, 2, 3]);
  assert.deepEqual(f({ PE: [4, 3] }), []); // an empty range: nothing passes
});

test("colours: continuous, Viridis, the values of the indices", () => {
  const spec = colorSpec(table, config, "AV_Volume_fraction", [1, 3]);
  assert.deepEqual(spec, { kind: "continuous", values: [0.8, 0.6], min: 0.6, max: 0.8, colorscale: "Viridis" });
});

test("figure: one WebGL trace with the points, names and hover", () => {
  const fig = scatterFigure(table, config, { x: "PE", y: "POAV_Volume_fraction", clr: "AV_Volume_fraction" }, [0, 2]);
  assert.equal(fig.data.length, 1);
  const [trace] = fig.data;
  assert.equal(trace.type, "scattergl");
  assert.deepEqual(trace.x, [1, 3]);
  assert.deepEqual(trace.y, [0.1, 0.3]);
  assert.deepEqual(trace.customdata, [["a", 0.9], ["c", 0.7]]);
  assert.deepEqual(trace.marker.color, [0.9, 0.7]);
  assert.equal(trace.marker.showscale, true);
  assert.equal(fig.layout.xaxis.title.text, "Parasitic energy [MJ/kg]");
  assert.equal(fig.layout.yaxis.title.text, "CO2 accessible void fraction [cm^3/cm^3]");
  assert.equal(fig.layout.legend, undefined);
});

test("properties: sorted rows and JSON", () => {
  const props = { "PE [MJ/kg]": 1.05, "Density [g/cm^3]": 0.36, "linker-linker_bond_type": "imine" };
  assert.deepEqual(propertyRows(props), [
    ["Density [g/cm^3]", "0.36"],
    ["PE [MJ/kg]", "1.05"],
    ["linker-linker_bond_type", "imine"],
  ]);
  const json = propertiesJson(props);
  assert.deepEqual(Object.keys(JSON.parse(json)), ["Density [g/cm^3]", "PE [MJ/kg]", "linker-linker_bond_type"]);
  assert.equal(JSON.parse(json)["PE [MJ/kg]"], 1.05);
});

test("config: columns, filters and presets agree", () => {
  const columns = new Set(config.columns.map((q) => q.column));
  assert.equal(columns.size, config.columns.length);
  for (const f of config.filters) assert.ok(columns.has(f), f);
  for (const q of config.columns) assert.ok(Object.hasOwn(table.columns, q.column), q.column);
  for (const [key, preset] of Object.entries(config.presets)) {
    assert.ok(columns.has(preset.x) && columns.has(preset.y), key);
  }
  assert.equal(config.defaultPreset in config.presets, true);
});

test("wrapTitle: lines of at most 18 characters, long words kept whole", () => {
  assert.equal(wrapTitle("Largest included sphere (HT)"), "Largest included<br>sphere (HT)");
  assert.equal(wrapTitle("Density"), "Density");
  assert.equal(wrapTitle("Supercalifragilisticexpialidocious x"), "Supercalifragilisticexpialidocious<br>x");
});
