GetFilesByExt
============
Version 0.1
[markmaz.com](http://wwww.markmaz.com)

Download all linked files by extension from a website
-----------------------------------------------------

*Wait a minute,* you say. *Doesn't* "wget -r -H -l1 -np -nd -A ext url" *already provide this facility?*

Yup! But wget isn't available by default on Macs and Windows. Macs do provide Python (and cURL), though. Therefore, this little ditty was written to enable downloads by extension without requiring the user to install anything (everyone already has [Python installed on Windows](http://diveintopython.org/installing_python/windows.html), right?...). No need to install wget from source/macports/etc if you like keeping your install vanilla, no need for browser addons, etc. 

How do I use this?
------------------

Glad you asked! After downloading the file, chmod +x GetFilesByExt.py to enable execution, then simply

<pre>
./GetFilesByExt url extension
</pre>

For example:
<pre>
./GetFilesByExt http://www.example.com/page/of/manypdflinks.html pdf
</pre>

This will download all linked pdf files from manypdflinks.html to whatever your current directory is. Feel free to add GetFilesByExt as an alias to your .bash_profile if you want fast access to it from wherever you are. 


What does this use?
-------------------

For downloading on Mac OS X, Python hands each link found on the page to cURL. If you run it on Windows, all the downloads are taken care of from within Python Standard Library provisions. 

Roadmap
-------
<b>0.4</b> Port to native Cocoa app

<b>0.3</b> GUI through TkInter or (for Mac) PyObjC?

<b>0.2</b> Add support for overwrite and resume

<b>0.1</b> Initial Release

Contact me for any suggestions/additions/corrections/requests: mark at markmaz.com
