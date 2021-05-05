#!/bin/bash
source cfg

### Download Osmosis
wget https://github.com/openstreetmap/osmosis/releases/download/$OSMOSIS_VERSION/osmosis-$OSMOSIS_VERSION.tgz
mkdir -p osmosis
cd osmosis && tar -xzf ../osmosis-$OSMOSIS_VERSION.tgz && cd ..
patch -s -N -p1 -d osmosis < ./osmosis.patch

### Download MapsForge
wget https://oss.sonatype.org/content/repositories/snapshots/org/mapsforge/mapsforge-map-writer/master-SNAPSHOT/mapsforge-map-writer-master-$MAPSFORGE_VERSION-jar-with-dependencies.jar
mkdir -p ~/.openstreetmap/osmosis/plugins
ln -s $PWD/mapsforge-map-writer-master-$MAPSFORGE_VERSION-jar-with-dependencies.jar ~/.openstreetmap/osmosis/plugins/

### Download POI Converter
git clone https://github.com/lieblerj/poi_converter

### Download Tag Mapping from Asamm (Locus Map)
wget https://github.com/asamm/mapsforge-v3-modded/raw/master/various/tag-mapping-xml/tag-mapping-tourist.xml

