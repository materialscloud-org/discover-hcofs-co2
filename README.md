# Discover-hcofs-co2

Hypothetical covalent organic frameworks (COFs) were screened for carbon capture. Nearly 400 COFs are identified with parasitic energy lower than that of an amine scrubbing process using monoethanolamine; over 70 are better performers than the best experimental COFs; and several perform similarly to Mg-MOF-74.

This repository contains a Docker buildable environment for building and serving the
**discover-hcofs-co2** visualiser of this data for the materials cloud website.

## Data

Data can be found on the [Materials Cloud Archive](https://archive.materialscloud.org/record/2020.0029/v1). The Aiida database is exceedingly large and will need to be built. This process may be tedious (both downloading and building) and thus its suggest that for local use to instead spin up the docker container.

##

The container sets up all dependencies, downloads the Aiida database, builds it and serves a Bokeh application for visualising this data. Since the dataset is so large, it can often take a while for the database to be populated on spin up of the docker image.

## Docker deployment

The requirements.txt file was build through uv and some of the packages are old. If you desire to rebuild this image from scratch it 'should' be simple, provided no packages have gone offline.

```
docker compose build
docker compose up
# open http://localhost:5006/figure
```

Alternatively a stored stable image is availible on the private MaterialsCloud harbor registry.

## For further devleopment

1. There is currently a very shaky, try:except clause that skips over the malformed entries (without any further reasoning). It would be nice to figure out why this dataset is malformed in the first place. If there are malformed entries maybe the dataset could be significantly reduced?

2. Some of the datasets seem to not render anything. They seem to have a .0 property that may have broke at some point. Could be nice to see if this data was ever populated and fix this.
