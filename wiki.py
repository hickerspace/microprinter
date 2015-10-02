#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, json, re, Image, logging
from websocket import create_connection
from urllib import urlencode, urlretrieve
from lxml import etree
from datetime import datetime
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
from microprinter import Microprinter


class WikipediaLive(object):
	def __init__(self):
		logging.basicConfig(
			level=logging.DEBUG,
			format="%(asctime)s %(levelname)-8s %(message)s",
			datefmt="%d.%m.%Y %H:%M:%S")
		self.ws = create_connection("ws://wikimon.hatnote.com/de/")
		self.printer = Microprinter("/dev/ttyUSB0")


	def stripHtmlTags(self, html):
		pars = HTMLParser()
		return pars.unescape(''.join(BeautifulSoup(html).findAll(text=True)))

	def monitor(self):
		while True:
			resp = json.loads(self.ws.recv())
			if not (resp["action"] == "edit" \
				and resp["change_size"] > 50 \
				and not resp["is_bot"] \
				and not resp["is_minor"] \
				and resp["ns"] == "Main"):

				continue

			date = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

			newEdit = "%s: %s editierte '%s' (%+d)\n" \
				% (date, resp["user"], resp["page_title"], resp["change_size"])
			self.printer.writeWrapped(newEdit.encode("utf-8"))
			logging.info(newEdit)

			getParams = urlencode({"title": resp["page_title"].encode("utf-8")})
			url = "http://de.wikipedia.org/w/index.php?%s" % getParams
			html = urllib2.urlopen(url).read()
			tree = etree.HTML(html)
			imgs = tree.xpath("//img[@class='thumbimage']")
			if len(imgs) > 0:
				imgUrl = "http:%s" % imgs[0].get("src")
				logging.info(imgUrl)
				self.printer.printImageFromFile(urlretrieve(imgUrl)[0], mode=0)

				captions = imgs[0].xpath("./../../div[@class='thumbcaption']")
				if len(captions) > 0:
					caption = etree.tostring(captions[0]).replace("\n", "")
					cleanCaption = "(%s)" % self.stripHtmlTags(caption)
					logging.info(cleanCaption)
					self.printer.writeWrapped(cleanCaption.encode("utf-8"))
			self.printer.write("\n\n\n")

if __name__ == "__main__":
	wiki = WikipediaLive()
	wiki.monitor()
