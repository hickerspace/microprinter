from xml.dom import minidom
import sys, time, urllib

from microprinter import Microprinter

m=Microprinter("/dev/ttyAMA0", "CBM1000")

if len(sys.argv) != 2:
    print "Please enter a search"
    raise SystemExit

search = sys.argv[1]

m.CBM1000_printMarkup("Search Term: *%s*" % search)

id = 0

while True:  

    url = "http://search.twitter.com/search.atom?rpp=50&q=%s&since_id=%s" % (search, id)

    xml = urllib.urlopen(url)

    doc = minidom.parse(xml)

    entries = doc.getElementsByTagName("entry")

    if len(entries) > 0:

        entries.reverse()

        for e in entries:

            title = e.getElementsByTagName("title")[0].firstChild.data
            pub = e.getElementsByTagName("published")[0].firstChild.data       
            id = e.getElementsByTagName("id")[0].firstChild.data.split(":")[2]
            name = e.getElementsByTagName("name")[0].firstChild.data.split(" ")[0]

            print "> " + name + ": " + title + " [" + pub + "]"
            m.CBM1000_printMarkup("[%s] *%s* %s" % (pub.encode("ascii", 'ignore'), name.encode("ascii", 'ignore'), title.encode("ascii", 'ignore')))

    time.sleep(360)
