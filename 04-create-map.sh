#!/bin/bash
source cfg

SRTM_FILE=SRTM/$COUNTRY-srtm.pbf
SRTM=""

NEWS_FILE=$COUNTRY-news.osm
NEWS=""

if [ -f "$SRTM_FILE" ]; then
	SRTM="--rb $SRTM_FILE --merge"
fi

if [ -f "$NEWS_FILE" ]; then
	NEWS="--rx $NEWS_FILE --merge"
fi

osmosis/bin/osmosis \
	--rb file=$PBF_FILE \
	--rx file="$ROUTES_FILE" --merge \
	$SRTM \
	$NEWS \
	--mapfile-writer tag-conf-file=tag-mapping-tourist.xml type=$MAPSFORGE_TYPE file=$MAP_FILE

