#!/bin/bash
source cfg

cp $LOCUS_POI_FILE $POI_FILE
sqlite3 $POI_FILE '.read append.sql'
python3 poi_converter/poiconverter.py -if pbf -om append $PBF_FILE $POI_FILE

