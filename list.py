#!/usr/bin/env python2

from __future__ import print_function
from getpass import getpass
from optparse import OptionParser
import sys
import time
from selenium import webdriver
from urllib import urlencode
from urlparse import urlparse, parse_qsl, parse_qs
import urlparse
from urllib import urlencode, urlretrieve
import urllib2
import hashlib
import base64
import requests
import os
#import common
import binascii
import logging
from selenium.webdriver.support.ui import Select
import re
import cgi # cgi.parse_header

def login_audible(driver, options, username, password, base_url, lang):
    # Step 1
    if '@' in username: # Amazon login using email address
        login_url = "https://www.amazon.com/ap/signin?"
    else:
        login_url = "https://www.audible.com/sign-in/ref=ap_to_private?forcePrivateSignIn=true&rdPath=https%3A%2F%2Fwww.audible.com%2F%3F" # Audible member login using username (untested!)
    if lang != "us": # something more clever might be needed
        login_url = login_url.replace('.com', "." + lang)
        base_url = base_url.replace('.com', "." + lang)
    player_id = base64.encodestring(hashlib.sha1("").digest()).rstrip() # keep this same to avoid hogging activation slots
    if options.player_id:
        player_id = base64.encodestring(binascii.unhexlify(options.player_id)).rstrip()
    logging.debug("[*] Player ID is %s" % player_id)
    payload = {'openid.ns':'http://specs.openid.net/auth/2.0', 'openid.identity':'http://specs.openid.net/auth/2.0/identifier_select', 
        'openid.claimed_id':'http://specs.openid.net/auth/2.0/identifier_select', 
        'openid.mode':'logout', 
        'openid.assoc_handle':'amzn_audible_' + lang, 
        'openid.return_to':base_url + 'player-auth-token?playerType=software&playerId=%s=&bp_ua=y&playerModel=Desktop&playerManufacturer=Audible' % (player_id)}
    query_string = urlencode(payload)
    url = login_url + query_string
    logging.info("Opening audible.com")
    driver.get(base_url + '?ipRedirectOverride=true')
    logging.info("Logging in to Amazon/Audible")
    driver.get(url)
    search_box = driver.find_element_by_id('ap_email')
    search_box.send_keys(username)
    search_box = driver.find_element_by_id('ap_password')
    search_box.send_keys(password)
    if os.getenv("DEBUG") or options.debug: # enable if you hit CAPTCHA or 2FA or other "security" screens
        logging.warning("[!] Running in DEBUG mode. You will need to login in a semi-automatic way, wait for the login screen to show up ;)")
        time.sleep(32)
    else:
        search_box.submit()

def configure_browser(options):
    logging.info("Configuring browser")

    
    opts = webdriver.ChromeOptions()
    
    # Chrome user agent will download files for us
    #opts.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36")
    
    # This user agent will give us files w. download info
    opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko")
    chromePrefs = {
        "profile.default_content_settings.popups":"0", 
        "download.default_directory":options.dw_dir}
    opts.add_experimental_option("prefs", chromePrefs)
    
    if sys.platform == 'win32':
        chromedriver_path = "chromedriver.exe"
    else:
        chromedriver_path = "./chromedriver"
    
    logging.info("Starting browser")
    
    driver = webdriver.Chrome(chrome_options=opts,
                              executable_path=chromedriver_path)
    
    return driver

class HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


def wait_for_download_or_die(datafile):
    retry = 0
    dw_sleep = 5
    while retry < 5 and not os.path.isfile(datafile):
        logging.info("%s not downloaded yet, sleeping %s seconds (retry #%s)" % (datafile, dw_sleep, retry))
        retry = retry + 1
        time.sleep(dw_sleep)
    if not os.path.isfile(datafile):
        logging.critical("Chrome used more than %s seconds to download %s, something is wrong, exiting" % (datafile,dw_sleep*retry,))
        sys.exit(1)

def print_progress(block_count, block_size, total_size):
    #The hook will be passed three arguments; 
    #    a count of blocks transferred so far, 
    #    a block size in bytes, 
    #    and the total size of the file. (may be -1, ignored) 

    prev_bytes_complete = (block_count-1)*block_size
    prev_percent = float(prev_bytes_complete)/float(total_size) * 100.0
    prev_progress = "%.0f" % prev_percent
    
    bytes_complete = block_count*block_size
    percent = float(bytes_complete)/float(total_size) * 100.0
    progress = "%.0f" % percent

    if (progress != prev_progress) and (block_count == 0 or int(progress) % 5 == 0 or int(progress) >= 100):
        logging.info("Download: %s%% (%s of %s bytes)" % \
                 (progress, 
                  bytes_complete, 
                  total_size))

def download_file(datafile, scraped_title, book, page, maxpage):
    with open(datafile) as f:
        logging.info("Parsing %s, creating download url" % datafile)
        lines = f.readlines()
        
    dw_options = parse_qs(lines[0])
    title = dw_options["title"][0]
    if title != scraped_title:
        logging.info("Found real title: %s" % (title,))
    logging.info("Parsed data for book '%s'" % (title,))
    
    url = dw_options["assemble_url"][0]
    
    params = {}
    for param in ["user_id","product_id","codec", "awtype","cust_id"]:
        params[param] = dw_options[param][0]
    
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(params)
    
    url_parts[4] = urlencode(query)
    
    url = urlparse.urlunparse(url_parts)
    logging.info("Book URL: %s" % url)
    
    logging.info("Downloading file data")
    head = urllib2.urlopen(HeadRequest(url))
    val, par = cgi.parse_header(head.info().dict['content-disposition']) 
    filename = par['filename'].split("_")[0]
    filename = filename + "." +  par['filename'].split(".")[-1]
    size = head.info().dict['content-length']
    
    logging.info("Filename: %s" % filename)
    logging.info("Size: %s" % size)
    
    path = "%s%s" % (options.dw_dir, filename)
    
    if os.path.isfile(path):
        logging.info("File %s exist, checking size", path)
        if int(size) == os.path.getsize(path):
            logging.info("File %s has correct size, not downloading" % (path,))
            return False
        else:
            logging.warning("File %s had unexpected size, downloading" % (path,))
    else:
        logging.info("File %s does not exist, downloading" % (path,))
    logging.info("Book %s of 20 on page %s of %s" % (book, page, maxpage))
    if True:
        urlretrieve(url, path, print_progress)
        logging.info("Completed download of '%s' to %s" % (title, path))
    else:
        logging.info("Completed download of '%s' to %s (not really)" % (title, path))
    return True

def wait_for_file_delete(datafile):
    os.remove(datafile)
    retry = 0
    dw_sleep = 2
    while retry < 5 and os.path.isfile(datafile):
        logging.info("%s not deleted, sleeping %s seconds (retry #%s)" % (datafile, dw_sleep, retry))
        retry = retry + 1
        time.sleep(dw_sleep)
    if os.path.isfile(datafile):
        logging.critical("OS used more than %s seconds to delete %s, something is wrong, exiting" % (datafile,dw_sleep*retry,))
        sys.exit(1)

def download_files_on_page(driver, page, maxpage, debug):
    books_downloaded = 0
    
    trs = driver.find_elements_by_tag_name("tr")
    for tr in trs:
        titles = tr.find_elements_by_name("tdTitle")
        for title_a in titles:
            #for a in td.find_elements_by_class_name("adbl-prod-title"):
            title = title_a.text.strip()
            if title != "":
                logging.info("Found book: '%s'" % (title,))
                if not debug:
                    #for author_ in tr.find_elements_by_class_name("adbl-library-item-author"):
                    #    print("Author (%s): '%s'" % (c, author_.text.strip()))
                    for download_a in tr.find_elements_by_class_name("adbl-download-it"):
                        #print("Download-title (%s): %s" % (c, download_a.get_attribute("title").strip()))
                            logging.info("Clicking download link for %s" % (title))
                            download_a.click()
                            logging.info("Waiting for Chrome to complete download of datafile")
                            time.sleep(1)
                            datafile = "%s%s" % (options.dw_dir, "admhelper")
                            wait_for_download_or_die(datafile)
                            
                            logging.info("Datafile downloaded")
        
                            books_downloaded = books_downloaded + 1
                            download_file(datafile, title, books_downloaded, page, maxpage)
                            wait_for_file_delete(datafile)
                            time.sleep(1)
                else:
                    books_downloaded = books_downloaded + 1
                    logging.info("Debug, no download")
                    time.sleep(1)
                                
                logging.info("looping through all download in spesific TR complete")
        #logging.info("looping through all tdTitle in spesific TR complete")
    logging.info("Downloaded %s books from this page" % (books_downloaded,))
    return books_downloaded

def configure_audible_library(driver):
    logging.info("Opening Audible library")
    driver.get("https://www.audible.com/lib")
    time.sleep(2)
    logging.info("Selecting books from 'All Time'")
    select = Select(driver.find_element_by_id("adbl_time_filter"))
    select.select_by_value("all")
    time.sleep(2)

    # Make sure we are getting the ENHANCED format
    # u'ENHANCED' u'MP332' u'ACELP16' u'ACELP85'
    s = Select(driver.find_element_by_id("adbl_select_preferred_format"))
    if len(s.all_selected_options) == 1:
        if 'ENHANCED' == s.all_selected_options[0].get_attribute("value").strip():
            logging.info("Selected format was ENHANCED, continuing")
        else:
            logging.info("Format was '%s', selecting 'ENHANCED'" % (s.all_selected_options[0].get_attribute("value"),))
            for opt in s.options:
                if "ENHANCED" == opt.get_attribute("value"):
                    opt.click()
                    time.sleep(5)
    else:
        logging.critical("Got more than one adbl_select_preferred_format.all_selected_options")
        sys.exit(1)

    if not ('adbl-sort-down' in driver.find_element_by_id("SortByLength").get_attribute("class")):
        logging.info("Sorting downloads by shortest to longest")
        driver.find_element_by_id("SortByLength").click()
        time.sleep(10)
    else:
        logging.info("Downloads were already sorted by shortest to longest, continuing")

def loop_pages(logging, driver):
    maxpage = 0
    for link in driver.find_elements_by_class_name("adbl-page-link"):
        maxpage = max(maxpage, int(link.text))
    
    books_downloaded = 0
    
    logging.info("Found %s pages of books" % maxpage)
    for pagenumz in range(maxpage):
        pagenum = pagenumz + 1
        
        logging.info("Scrolling to bottom of page because javascript")
        for x in range(3):
            # Page is not loaded before we scroll
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        logging.info("Downloading books on page %s" % (pagenum,))
        books_downloaded = books_downloaded + download_files_on_page(driver, pagenum, maxpage, debug=False)
        time.sleep(5)
        found_next = False
        logging.info("Looking for link to next page (page %s)" % (pagenum + 1,) )
        lis = driver.find_elements_by_class_name("adbl-pagination")
        for li in lis:
            ls = li.find_elements_by_class_name("adbl-link")
            for l in ls:
                if l.text.strip() == "%s" % ((pagenum + 1),):
                    logging.info("Clicking link for page %s" % ((pagenum + 1),))
                    found_next = True
                    l.click()
                    break;
            if found_next:
                break;

    logging.info("Downloaded or skipped a total of %s books" % (books_downloaded,))

if __name__ == "__main__":
    parser = OptionParser(usage="Usage: %prog [options]", version="%prog 0.2")
    parser.add_option("-d", "--debug",
                      action="store_true",
                      dest="debug",
                      default=False,
                      help="run program in debug mode, enable this for 2FA enabled accounts or for authentication debugging")
    parser.add_option("-l", "--lang",
                      action="store",
                      dest="lang",
                      default="us",
                      help="us (default) / de / fr",)
    parser.add_option("-p",
                      action="store",
                      dest="player_id",
                      default=None,
                      help="Player ID in hex (optional)",)
    parser.add_option("-w",
                      action="store",
                      dest="dw_dir",
                      default="/tmp/audible",
                      help="Download directory (must exist)",)
    
    logging.basicConfig(format='%(levelname)s(#%(lineno)d):%(message)s', level=logging.INFO)
    
    (options, args) = parser.parse_args()
    
    if not options.dw_dir.endswith(os.path.sep):
        options.dw_dir += os.path.sep
    
     
    username = raw_input("Username: ")
    password = getpass("Password: ")
    
    base_url = 'https://www.audible.com/'
    base_url_license = 'https://www.audible.com/'
    lang = options.lang
    
    driver = configure_browser(options)
    
    login_audible(driver, options, username, password, base_url, lang)
    configure_audible_library(driver)
    loop_pages(logging, driver)

    logging.info("Awating input, master: ")
    #driver.quit()
    #quit()