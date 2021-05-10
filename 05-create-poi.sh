#!/bin/bash
source cfg

python3 poi_converter/poiconverter.py -if pbf -om create $PBF_FILE $POI_FILE

