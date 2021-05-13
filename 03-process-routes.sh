#!/bin/bash
source cfg

osmosis/bin/osmosis \
	--rb $PBF_FILE \
	--log-progress \
	--tag-filter accept-relations route=hiking \
	--used-way \
	--rb $PBF_FILE \
	--log-progress \
	--tag-filter accept-relations route=foot \
	--used-way \
	--rb $PBF_FILE \
	--log-progress \
	--tag-filter accept-relations route=bicycle \
	--used-way \
	--rb $PBF_FILE \
	--log-progress \
	--tag-filter accept-relations route=mtb \
	--used-way \
	--rb $PBF_FILE \
	--log-progress \
	--tag-filter accept-relations route=historic \
	--used-way \
	--merge \
	--merge \
	--merge \
	--merge \
	--write-xml $ROUTES_FILE

python3 parse-routes.py $ROUTES_FILE

