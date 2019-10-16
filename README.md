Based on code from https://github.com/inAudible-NG/audible-activator

# HOWTO download.py

 * (if you don't have pip: sudo apt-get install python-pip)
 * pip install requests
 * pip install selenium

Download and extract the correct ChromeDriver zip file from 
https://sites.google.com/a/chromium.org/chromedriver/downloads
to the script folder

Default download dir is /tmp/audible, change with -w, I'm usure
if spaces are supported

You are free to minimize the browser window while downloading, but do
not click or navigate in it

The script supports a lazy format of restart.

# IMPORTANT

We trick Audible to think that we want to download files
using Audible Download Manager. If "software verification"
is on, Audible apparently tries to detect if you have
it installed, and will fail. To get proper downloads,
turn off software verification in your Audible settings.

### .com:
* Hi, <yourname>
  * Account Details
    * Software verification

### .de:
* Hallo, <yourname>
  * Mein Konto
    * Einstellungen
      * Software-Überprüfung

# KNOWN BUGS
## Unresonable number of pages of books
Sometimes lists a unresonable number of pages of books, i.e:
```INFO(#282):Found 47 pages of books``` when you expected
```INFO(#282):Found 15 pages of books```
* Fix: Ctrl+c while "INFO(#286):Scrolling to bottom of page because javascript"
and restart

# Download error
Download error ```KeyError: 'content-disposition'```
* You probably hit "Download limit for untargeted content reached."
* Fix: This was probably fixed by starting to lie in our User-Agent. If not, probably wait 30 min and restart

# HOWTO loop_remove_drm.sh

Script for removing drm from all audible *.aax-files in a folder.
* Requires a ffmpeg new enough to support -activation_bytes avaliable
* Requires exiftool to be installed. 
  * Mac: "brew install exiftool"
  * Linux (apt): sudo apt install libimage-exiftool-perl
* A config file will be created the first time you run the script
  * Configure the variables ACTIVATION_BYTES, FROM, TO and FFMPEG to fit your system
    * You find ACTIVATION_BYTES by using https://github.com/inAudible-NG/audible-activator
