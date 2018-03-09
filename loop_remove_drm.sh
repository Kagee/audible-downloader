#! /bin/bash

ACTIVATION_BYTES="<add your bytes here>"
FROM="/tmp/audible"
TO="/tmp/audible-no-drm"
FFMPEG="ffmpeg" # Path to ffmpeg that supports -activation_bytes

COUNT_FROM="$(ls "$FROM" | wc -l)"

# only aax, something fails with .aa, and i'm not up to debugging
for FROMPATH in $FROM/*.aax; do 
  #echo "$FROMPATH";
  TOPATH="$TO/$(basename "$FROMPATH" | cut -d'_' -f 1).mp4"
  if [ ! -e "$TOPATH" ]; then
    echo "$FROMPATH => $TOPATH"
    $FFMPEG -loglevel error  -activation_bytes "$ACTIVATION_BYTES" -i "$FROMPATH" -vn -c:a copy "$TOPATH"
  else
    echo "$TOPATH found, skipping"
  fi
done

COUNT_TO="$(ls "$TO" | wc -l)"

if [ "$COUNT_FROM" -gt "$COUNT_TO" ]; then
  echo "$COUNT_FROM sourcefiles, $COUNT_TO destination files, possible error in conversion or duplicate title";
fi
