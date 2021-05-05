#!/bin/bash
source cfg
osmosis/bin/osmosis --rb file=$PBF_FILE --rx file="$ROUTES_FILE.xml" --merge --mapfile-writer tag-conf-file=tag-mapping-tourist.xml file=$MAP_FILE

