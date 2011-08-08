#!/usr/bin/env python

# NOTE: GetFilesByExt uses Popen instead of os.system() since the
# argument inputs are coming from the internets and coldhearted injections
# can be easily introduced otherwise. The files you download and the site
# you download from are themselves not compared against any
# malware-prevention sources however. Only use GetFilesByExt with sites
# you trust. 

########################################################################
#                         GetFilesByExt v0.1                           #
#                       (c) 2011 Mark Mazumder                         #
#                             markmaz.com                              #
########################################################################

from HTMLParser import HTMLParser
import urllib  #these imports are not kosher for python 3
import urllib2
import urlparse
import shlex
import re
import sys
import os
import subprocess


class Downloadable(object):
    def __init__(self, target):
        self._target = target
        #Form a filename by looking at the last path component and removing the %20s etc
        fn = target.split('/')[-1]
        self._filename = urllib.unquote(fn)

    @property
    def target(self):
        """URL to the downloadable resource"""
        return self._target

    @property
    def filename(self):
        """Filename of the downloadable resource"""
        #Maybe raise exception if not isalnum() depending on filesystem support here
        return self._filename

class DownloadHandler(object):
    """ Are we on Mac OSX? Use Curl! Are we on windows? Download
        using urllib2. Are we on Linux? man wget, silly! But
        urllib2 will suffice for now.
    """
    def __init__(self):
        self.list_downloads = []
        self.download_handler = None
        #too lazy to search user path myself, let which do the work for now
        check_curl = None
        try:
            check_curl = subprocess.Popen(["which", "curl"], stdout=subprocess.PIPE).communicate()[0]
        except OSError:
            #windows...
            pass
        if not check_curl:
            self.download_handler = self.uldl
        else:
            self.download_handler = self.curldl

    def do_downloads(self):
        for downloadable in self.list_downloads:
            if os.path.isfile(downloadable.filename):
                #can request user input for overwrite, or can enable resuming if desired
                print "File {0} already exists, continuing".format(downloadable.filename)
            else:
                print "Starting download of {0}".format(downloadable.filename)
                self.download_handler(downloadable)

    def register_download(self, target):
        self.list_downloads.append(Downloadable(target))

    def curldl(self, downloadable):
        #Avoid the %20s in the filename that occur when using "curl -O" + downloadable.target
        curl = subprocess.Popen(shlex.split("curl {0} --output \"{1}\"".format(downloadable.target, downloadable.filename)))

        # wait for stderr progress bar from curl to finish - if modified
        # to use subprocess.PIPE, change to Popen.communicate to avoid
        # deadlock
        curl.wait()

    def uldl(self, downloadable):
        """Uses urllib for downloading and reporting via hook -> to change in python 3"""
        def status_print(blocks_so_far, block_sz, total_sz):
            dbl_percent = 100 * float(blocks_so_far * block_sz)/total_sz
            percent_str = lambda pct: str(pct).split('.')[0] if pct <= 100. else str(100) 
            status = "{0:>3}% downloaded out of {1} KB".format(percent_str(dbl_percent), total_sz/1024)
            sys.stdout.write("\r" + status)
            sys.stdout.flush()
        urllib.urlretrieve(url=downloadable.target, filename=downloadable.filename, reporthook=status_print)
        sys.stdout.write("\n")

    def ul2dl(self,downloadable):
        """A urllib2 downloader - bonus option if python's urllib user agent isn't recognized.
           Version 0.2 will check for HTTP return code errors and automatically switch to this.
        """
        req = urllib2.Request(url=downloadable.target, headers={"User-Agent" : "Chrome/13.0.782.107"})
        cxn = urllib2.urlopen(req)
        filesize = int(cxn.info().getheader("Content-Length"))
        print "Starting download of {0}, {1} KB Total".format(downloadable.filename, filesize / 1024)
        blocksize = 16384
        fh = open(downloadable.filename, 'wb')
        while True:
            buf = cxn.read(blocksize)
            if not buf:
                break
            fh.write(buf)
        fh.close()


class ExtensionDownloadParser(HTMLParser):
    #old-style class: can't use properties, lacks simple support for super in init. will change when py3 hits macs
    _extension = None
    def set_extension(self, ext):
        """Ensure extension is valid for an re"""
        if not ext.isalnum():
            raise ValueError("The extension {0} must be alphanumeric - (\"pdf\", \"jpg\")".format(ext))
        self._extension = ext
    
    parent_url = None
    register_link_to_download = None

    #_downloader = None
    #@property
    #def register_link_to_download(self):
    #    """Preferred download handler on our system"""
    #    return self._downloader

    #@register_link_to_download.setter
    #def register_link_to_download(self, dl_hdl):
    #    self._downloader = dl_hdl

    #_parent_url = None
    #@property
    #def parent_url(self):
    #    """An absolute URL to know where to download relative links in handle_starttag"""
    #    return self._parent_url

    #@parent_url.setter
    #def parent_url(self, url):
    #    self._parent_url = url

    #_extension = None
    #@property
    #def extension(self):
    #    """For all the links found on the parent page, download the ones with this extension"""
    #    return self._extension
    #
    #@extension.setter
    #def extension(self, ext):
    #    """Ensure extension is valid for an re"""
    #    #feel free to add further validations here
    #    if not ext.isalnum():
    #        raise ValueError("The extension {0} is in the wrong format - (\"pdf\", \"jpg\")".format(ext))
    #    self._extension = ext

    def handle_starttag(self, tag, attrs):
        if tag == 'a' or tag == 'img':
            link = None
            for elem in attrs:
                if elem[0] == 'href':
                    link = elem[1]
                    break
            if not link:
                return
            match = re.search(r'\.' + self._extension + r'\b', link)
            if match:
                #If given an absolute URL, split and quote only the path, then rejoin, preserving the scheme.
                splitres = urlparse.urlsplit(link)
                link = urlparse.urlunsplit((splitres.scheme, splitres.netloc, urllib.quote(splitres.path), splitres.query, splitres.fragment))
                # If the URL is relative, create an absolute URL. If already absolute, urljoin will not modify it.
                abs_link = urlparse.urljoin(self.parent_url, link)
                self.register_link_to_download(abs_link)

def kill_err(msg):
    print msg
    exit()

def main(input_url, extension):
    parent_req = urllib2.Request(url=input_url, headers={"User-Agent" : "Chrome/13.0.782.107"})
    parent_page = None
    try:
        parent_page = urllib2.urlopen(parent_req)
    except urllib2.HTTPError as e:
        kill_err("HTTP Error code {0}".format(e.code))
    except urllib2.URLError as e:
        kill_err(e.reason)
    parent_html = parent_page.read()
    parent_parser = ExtensionDownloadParser()
    downloader = DownloadHandler()
    try:
        parent_parser.set_extension(extension)
        #in order to handle relative links in case we've been redirected from input_url after req
        parent_parser.parent_url = parent_page.geturl() 
        parent_parser.register_link_to_download = downloader.register_download
    except ValueError as e:
        kill_err(e)

    #Parse the page for downloadable links - the handler will register them to downloader
    parent_parser.feed(parent_html) 

    #Get to work on the downloading
    downloader.do_downloads()
    
if __name__ == '__main__':
    if len(sys.argv) != 3:
        kill_err("usage: ./GetFilesByExt url extension\nExample: ./GetFilesByExt http://www.example.com/page/of/manypdflinks.html pdf")
    main(sys.argv[1], sys.argv[2])
