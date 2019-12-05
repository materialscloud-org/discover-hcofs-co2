[![Build Status](https://travis-ci.org/materialscloud-org/structure-property-visualizer.svg?branch=master)](https://travis-ci.org/materialscloud-org/structure-property-visualizer)

# Structure-Property-Visualizer

Use this app to generate interactive visualizations like [these](https://www.materialscloud.org/discover/cofs#mcloudHeader)
for atomic structures and their properties.

## Inner working

There are two kind of groups:
* `group_ht_{COF-name}` for ca. 66,800 COFs computed with HT approach
* `group_pe_{COF-name}` for ca. 800 COFs for which PE is computed
The nodes of these group have a tag which is stored as the `extra` with key `'group_tag'`.
The first group, `group_ht_{COF-name}`, contains the tags:
```
'orig_cif'    # CIF input of the HT work chain
'ht_wc'       # High-throughput work chain
'ht_geom_out' # Zeo++'s output Dict
'ht_kh_out1'  # Raspa's output Dict with global info
'ht_kh_out2'  # Raspa's output Dict with component (CO2) info
```
While the seconds, `group_pe_{COF-name}`, contains the tags:
```
'orig_cif'    # CIF input of both CO2 and N2 VolpoKhIsotherm work chain
'isot_co2_wc' # VolpoKhIsotherm work chain for CO2
'isot_n2_wc'  # VolpoKhIsotherm work chain for N2
'isot_n2_out' # VolpoKhIsotherm's output Dict for CO2
'isot_n2_out' # VolpoKhIsotherm's output Dict for N2
'ht_wc'       # (same as the ht group)
'ht_geom_out' # (same as the ht group)
'ht_kh_out1'  # (same as the ht group)
'ht_kh_out2'  # (same as the ht group)
```
## Re-implementation based on Panel

Use as jupyter notebook:
```
jupyter notebook
# open figure/main.ipynb
```

Use with panel:
```
panel serve detail/ figure/
```

## Features

 * interactive scatter plots via [bokeh server](https://bokeh.pydata.org/en/1.0.4/)
 * interactive structure visualization via [jsmol](https://chemapps.stolaf.edu/jmol/docs/)
 * simple input: provide CIF/XYZ files with structures and CSV file with their properties
 * simple deployment on [materialscloud.org](https://www.materialscloud.org/discover/menu) through [Docker containers](http://docker.com)
 * driven by database backend:
   1. [sqlite](https://www.sqlite.org/index.html) database (default)
   1. [AiiDA](http://www.aiida.net/) database backend (less tested)

## Getting started

### Prerequisites

 * [git](https://git-scm.com/)
 * [python](https://www.python.org/) >= 2.7
 * [nodejs](https://nodejs.org/en/) >= 6.10

### Installation

```
git clone https://github.com/materialscloud-org/structure-property-visualizer.git
cd structure-property-visualizer
pip install -e .     # install python dependencies
./prepare.sh         # download test data (run only once)
```

### Running the app

```
bokeh serve --show figure # run app
```

## Customizing the app

### Input data
 * a set of structures in `data/structures`
   * Allowed file extensions: `cif`, `xyz`
 * a CSV file `data/properties.csv` with their properties
   * has a column `name` whose value `<name>` links each row to a file in `structures/<name>.<extension>`.
 * adapt `import_db.py` accordingly and run it to create the database

### Plots

The plots can be configured using a few YAML files in `figure/static`:
 * `columns.yml`: defines metadata for columns of CSV file
 * `filters.yml`: defines filters available in plot
 * `presets.yml`: defines presets for axis + filter settings

## Docker deployment

```
pip install -e .
./prepare.sh
docker-compose build
docker-compose up
# open http://localhost:3245/cofs/select-figure
```
