#! /bin/bash
CONFIG="./loop_remove_drm.conf"
if [ ! -f "$CONFIG" ]; then
 echo 'ACTIVATION_BYTES="<your personal activation bytes>"' > "$CONFIG"
 echo 'FROM="<absolute path to input folder>"' >> "$CONFIG"
 echo 'TO="<absolute path to output folder>"' >> "$CONFIG"
 echo "FFMPEG=\"<path to ffmpeg that supports "\
     "-activation_bytes, possibly only 'ffmpeg'\"" >> "$CONFIG"
 echo "Please edit $CONFIG, then run script again"
 exit
fi 

source "$CONFIG"

if [ "<your personal activation bytes>" == "$ACTIVATION_BYTES" ]; then
    echo "You didn't edit $CONFIG as i told you, did you?"
exit 2
fi

# admhelper might be here if we aborted the download
COUNT_FROM="$(ls "$FROM" | grep -v admhelper | wc -l)"
echo "$COUNT_FROM"

# only aax, something fails with .aa, and i'm not up to debugging
for FROMPATH in $FROM/*.aax; do
  #Get Exif data from the file
  ARTIST="`exiftool -m -Artist "$FROMPATH" -p '$Artist'`"
  TITLE="`exiftool -m -Title "$FROMPATH" -p '$Title'`"
  #Store Artist Path for mkdir
  ARTISTPATH="$TO"/"$ARTIST"
  #Update TOPATH to include Artist and Title data from exiftool
  TOPATH="$ARTISTPATH"/"$TITLE".m4b
  echo "TOPATH: $TOPATH"


  if [ ! -e "$TOPATH" ]; then
    echo "$FROMPATH => $TOPATH"
    mkdir -p -- "$ARTISTPATH"
    echo $FFMPEG -loglevel error  -activation_bytes "$ACTIVATION_BYTES" -i "$FROMPATH" -c:a copy -vn -f mp4 "$TOPATH"
    $FFMPEG -loglevel error  -activation_bytes "$ACTIVATION_BYTES" -i "$FROMPATH" -c:a copy -vn -f mp4 "$TOPATH"
  else
    echo $FFMPEG -loglevel error  -activation_bytes "$ACTIVATION_BYTES" -i "$FROMPATH" -c:a copy -vn -f mp4 "$TOPATH"
    "$TOPATH found, skipping"
  fi
done

#Update COUNT_TO to check for files in subdirectories (Ignoring DS_Store files on MacOS)
COUNT_TO="$(find "$TO" -type f | grep -v .DS_Store | wc -l)"

if [ "$COUNT_FROM" -gt "$COUNT_TO" ]; then
  echo "$COUNT_FROM sourcefiles, $COUNT_TO destination files, possible error in conversion or duplicate title";
fi
