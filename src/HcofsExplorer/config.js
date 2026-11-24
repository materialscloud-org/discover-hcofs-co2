// The configuration of this app: the old app's figure/static/{columns,filters,presets}.yml (commit f95d38b)
// as one object, in the format src/common/ reads. The data is made by
// scripts/prepareForFrontend.py (its column list is the same as `columns` here).

// Where the shards of public/data/details/ are chosen (scripts/prepareForFrontend.py: SHARDS)
export const SHARD_COUNT = 16384;

export const config = {
  title: "Hypothetical COFs for CO2 Capture",
  itemName: "COFs", // in messages: "12 of 66852 COFs"
  dois: ["10.24435/materialscloud:2020.0029/v1"],
  // Materials Cloud Explore of this AiiDA database: the COF page links its CIF node there
  explore: "https://www.materialscloud.org/explore/hcofs-co2",
  shardCount: SHARD_COUNT,

  // type "float": a numeric column (a plot axis, a colour, a range filter).
  // The ranges are only the ends of the filter sliders: a range is not a bound on the plot.
  columns: [
    { column: "PE", type: "float", label: "Parasitic energy", range: [0, 5], unit: "MJ/kg" },
    { column: "WCg", type: "float", label: "Gravimetric working capacity", range: [0, 10], unit: "kg CO2 / kg" },
    { column: "WCv", type: "float", label: "Volumetric working capacity", range: [0, 100], unit: "kg CO2 / m^3" },
    { column: "Pur", type: "float", label: "Final CO2 purity", range: [0, 1], unit: "mol/mol" },
    // Td and Pd: desorption temperature and pressure (pe_out)
    { column: "Td", type: "float", label: "Desorption temperature", range: [330, 360], unit: "K" },
    { column: "Pd", type: "float", label: "Desorption pressure", range: [0.03, 0.15], step: 0.001, unit: "bar" },
    { column: "henry_coefficient_average_ht", type: "float", label: "CO2 Henry coefficient (HT)", range: [0, 1], unit: "mol/kg/Pa" },
    { column: "henry_coefficient_average_n2", type: "float", label: "N2 Henry coefficient", range: [0, 1], unit: "mol/kg/Pa" },
    { column: "POAV_Volume_fraction", type: "float", label: "CO2 accessible void fraction", range: [0, 1], unit: "cm^3/cm^3" },
    { column: "POAV_cm^3/g", type: "float", label: "CO2 accessible pore volume", range: [0, 1], unit: "cm^3/g" },
    // columns.yml says 10-1200 g/cm^3: the values are 0.1-1.1 g/cm^3
    { column: "Density", type: "float", label: "Density (HT)", range: [0, 1.5], unit: "g/cm^3" },
    { column: "Channels.Largest_included_spheres.0", type: "float", label: "Largest included sphere (HT)", range: [0, 50], unit: "Angs" },
    { column: "Channels.Largest_free_spheres.0", type: "float", label: "Largest free sphere (HT)", range: [0, 50], unit: "Angs" },
    // columns.yml says 0-50 cm^3/cm3, but a void fraction is between 0 and 1
    { column: "AV_Volume_fraction", type: "float", label: "N2-probe-center void fraction (HT)", range: [0, 1], unit: "cm^3/cm^3" },
  ],

  // filters.yml, in this order
  filters: ["PE", "Td", "Pd"],

  // list columns that can colour the points, with the colour of each value: none here
  // (every float column can colour them, Viridis)
  categoryColors: {},

  // presets.yml: x, y, clr and the filters that differ from "everything"
  defaultPreset: "default",
  presets: {
    default: { clr: "AV_Volume_fraction", x: "PE", y: "POAV_Volume_fraction" },
    sensible: { clr: "Td", x: "Pd", y: "PE" },
  },
};
