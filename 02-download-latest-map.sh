#!/bin/bash
source cfg

rm -f $PBF_FILE
curl http://download.geofabrik.de/$CONTINENT/$PBF_FILE --output $PBF_FILE

