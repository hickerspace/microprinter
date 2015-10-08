#!/usr/bin/env python

"""
	Library for TEC TRST-53 printers based on Ben O'Steen's Python port
	(https://github.com/benosteen/microprinter) from original Ruby code
	by Roo Reynolds (https://github.com/rooreynolds/microprinter and
	http://rooreynolds.com/category/microprinter/).

	+ deleted some functionality not relevant for the TEC TRST-53
	+ customized methods for the TEC TRST-53
	+ object-oriented image printing
	+ QR code functionality added

	See also: http://microprinter.pbwiki.com/
"""

from serial import Serial
import qrcode, textwrap
try:
	import Image
except ImportError:
	from PIL import Image

CBMCOMMANDS = {
	"COMMAND" : 0x1B,						"LF" : 0x10,
	"LINEFEED_RATE" : 0x33,					"FULLCUT" : [0x1B,0x69],
	"PARTIALCUT" : [0x1B,0x6D],				"PRINT_MODE" : 0x21,
	"DOUBLEPRINT" : 0x47,					"UNDERLINE" : 0x2D,
	"RESET" : 0x40,							"COMMAND_IMAGE" : 0x2A,
	"COMMAND_FLIPCHARS" : 0x7B,				"COMMAND_ROTATECHARS" : 0x56,
	"COMMAND_BARCODE" : 0x1D,				"COMMAND_BARCODE_PRINT" : 0x6B,
	"COMMAND_BARCODE_WIDTH" : 0x77,			"COMMAND_BARCODE_HEIGHT" : 0x68,
	"COMMAND_BARCODE_TEXTPOSITION" : 0x48,	"COMMAND_BARCODE_FONT" : 0x66,
	"BARCODE_WIDTH_NARROW" : 0x02,			"BARCODE_WIDTH_MEDIUM" : 0x03,
	"BARCODE_WIDTH_WIDE" : 0x04,			"BARCODE_TEXT_NONE" : 0x00,
	"BARCODE_TEXT_ABOVE" : 0x01,			"BARCODE_TEXT_BELOW" : 0x02,
	"BARCODE_TEXT_BOTH" : 0x03,				"BARCODE_MODE_UPCA" : 0x00,
	"BARCODE_MODE_UPCE" : 0x01,				"BARCODE_MODE_JAN13AEN" : 0x02,
	"BARCODE_MODE_JAN8EAN" : 0x03,			"BARCODE_MODE_CODE39" : 0x04,
	"BARCODE_MODE_ITF" : 0x05,				"BARCODE_MODE_CODEABAR" : 0x06,
	"BARCODE_MODE_CODE128" : 0x07
}

class Microprinter(object):
	def __init__(self, serialPort="/dev/ttyUSB0", baudrate=19200):
		self.c = CBMCOMMANDS
		self.feed = self.CBMfeed
		self.printer = Serial(serialPort, baudrate)

	def CBMfeed(self, lines=1):
		if lines and isinstance(lines, int):
			lines = lines % 256
			for x in xrange(lines):
				self.write("\n\n")
		else: self.write("\n\n")
		self.flush()

	def close(self):
		self.printer.close()

	def sendcodes(self, *args):
		"""Will turn any set of integers to the printer directly:"""
		self.printer.write("".join(map(chr, args)))

	def write(self, message):
		self.printer.write(message)

	def writeWrapped(self, message):
		self.printer.write(textwrap.fill(message, 24))

	def flush(self):
		self.printer.flush()

	def printUPCABarcode(self, barcode):
		allowed = "0123456789"
		barcode = "".join([x for x in barcode if x in allowed])
		if 10 < len(barcode) < 13:
			print "UPC-A barcodes must be between 11 and 12 'digits'"
			return
		self.printBarcode(barcode, self.c['BARCODE_MODE_UPCA'])

	def printBarcode(self, barcode, width=3, height=162, barcodeMode = None):
		if not barcodeMode: barcodeMode = self.c['BARCODE_MODE_UPCA']
		self.setBarcodeHeight(height)
		self.setBarcodeWidth(width)
		self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_PRINT'])
		self.sendcodes(barcodeMode)
		self.write(barcode)
		self.sendcodes(0x00) # NUL code

	def setBarcodeHeight(self, height=162):
		height = height % 256
		self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_HEIGHT'])
		self.sendcodes(height)
		self.flush()

	def setBarcodeWidth(self, width=3):
		if (width < 2): width = 2
		if (width > 4): width = 4
		self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_WIDTH'])
		self.sendcodes(width)
		self.flush()

	def resetState(self):
		self.sendcodes(self.c['COMMAND'], self.c['RESET'])
		self.flush()

	def cut(self):
		self.sendcodes(*self.c['FULLCUT'])

	def partialCut(self):
		self.sendcodes(*self.c['PARTIALCUT'])

	def setDoubleprint(self, state=True):
		self.sendcodes(self.c['COMMAND'], self.c['DOUBLEPRINT'])
		if state: self.sendcodes(0x01)
		else: self.sendcodes(0x00)
		self.flush()

	def setUnderline(self, state=True):
		self.sendcodes(self.c['COMMAND'], self.c['UNDERLINE'])
		if state: self.sendcodes(0x01)
		else: self.sendcodes(0x00)
		self.flush()

	def setBarcodeTextPosition(self, position):
		if position < 0: position = 0
		if position > 3: position = 3
		self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_TEXTPOSITION'])
		self.sendcodes(position)
		self.flush()

	def setBarcodeFont(self, fontcode):
		if fontcode < 0: fontcode = 0
		if fontcode > 1: fontcode = 1
		self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_FONT'])
		self.sendcodes(fontcode)
		self.flush()

	def printImagebytes(self, m, data):
		self.sendcodes(self.c['COMMAND'], self.c['COMMAND_IMAGE'])
		density = 1
		if m == 1 or m == 33: density = 3
		datalength = len(data) / density
		self.sendcodes(m, datalength%256, datalength/256)
		self.sendcodes(*data)
		self.flush()

	def setLineFeedRate(self, feedlength):
		# <1B>H<33>H<n>
		self.sendcodes(self.c['COMMAND'], self.c['LINEFEED_RATE'])
		self.sendcodes(feedlength)
		self.flush()

	def printImageRow(self, data, mode):
		bytes_ = []
		if mode < 2:
			for x in range(len(data[0])):
				byteCol = data[0][x] << 7|data[1][x] << 6|data[2][x] << 5|data[3][x] << 4|data[4][x] << 3|data[5][x] << 2|data[6][x] << 1|data[7][x]
				bytes_.append(byteCol ^ 255)
		else:
			for x in range(len(data[0])):
				byteCol = data[0][x] << 7|data[1][x] << 6|data[2][x] << 5|data[3][x] << 4|data[4][x] << 3|data[5][x] << 2|data[6][x] << 1|data[7][x]
				bytes_.append(byteCol ^ 255)
				byteCol = data[8][x] << 7|data[9][x] << 6|data[10][x] << 5|data[11][x] << 4|data[12][x] << 3|data[13][x] << 2|data[14][x] << 1|data[15][x]
				bytes_.append(byteCol ^ 255)
				byteCol = data[16][x] << 7|data[17][x] << 6|data[18][x] << 5|data[19][x] << 4|data[20][x] << 3|data[21][x] << 2|data[22][x] << 1|data[23][x]
				bytes_.append(byteCol ^ 255)
		self.printImagebytes(mode, bytes_)

	def printImageFromFile(self, path, width=288, mode=0, autorotate=True, dither=True):
		im = Image.open(path)
		self.printImage(im, width, mode, autorotate, dither)

	def printQrCode(self, text):
		qr = qrcode.QRCode(version=4, box_size=4, border=1)
		qr.add_data(text)
		qr.make(fit=True)
		qrImg = qr.make_image()
		self.printImage(qrImg, autorotate=False)

	def printImage(self, im, width=288, mode=0, autorotate=True, dither=True):
		self.setLineFeedRate(1)
		rowlimit = 8
		fudgefactor = 0.66
		if mode > 1:
			rowlimit = 24
			fudgefactor = 1.0
		if dither: im = im.convert("1", dither = Image.FLOYDSTEINBERG)
		else: im = im.convert("1")
		size = im.size
		# Landscape ratio
		if autorotate and size[0] > size[1]: im = im.transpose(Image.ROTATE_90)
		resizeRatio = (float(width)/im.size[0])*fudgefactor # fudge factor for scaling
		im = im.resize((width, int(resizeRatio * im.size[1])))
		lbuffer = []
		rows = 0
		columns = 0
		cbuffer = []
		for pixel in im.getdata():
			columns = columns + 1
			if pixel > 128: cbuffer.append(1)
			else: cbuffer.append(0)
			if columns == width:
				lbuffer.append(cbuffer)
				cbuffer = []
				columns = 0
				if len(lbuffer) == rowlimit:
					self.printImageRow(lbuffer, mode)
					#sleep(0.2)
					lbuffer = []
					rows = rows + 1
		if 0 < len(lbuffer) < rowlimit:
			lbuffer.extend([[1]*width]*(rowlimit-len(lbuffer)))
			self.printImageRow(lbuffer, mode)
			#sleep(0.2)
		self.resetState()

