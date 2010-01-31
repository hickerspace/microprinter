#!/usr/bin/env python

# Ported from code created by Roo Reynolds
# http://rooreynolds.com/category/microprinter/

# See also: http://microprinter.pbwiki.com/

from serial import Serial

import logging

logger = logging.getLogger("Microprinter")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)

class NoSerial(Exception):
  pass

class BarcodeException(Exception):
  pass

class CBM1000Mode(object):
  """CBM1000Mode.E - emphasis
  CBM1000Mode.DH - double height
  CBM1000Mode.DW - double width
  CBM1000Mode.U - underline
  Examples:
  
  # Use font A with double-width
  Microprinter.setPrintMode(0|CBM1000Mode.DW)
  # Use font B with emphasis and double-height
  Microprinter.setPrintMode(1|CBM1000Mode.E|CBM1000Mode.DH)
  """
  E = 1 << 3
  DH = 1 << 4
  DW = 1 << 5
  U = 1 << 7

def decorator_shell(decorator):
  def new_decorator(f):
    g = decorator(f)
    g.__name__ = f.__name__
    g.__doc__ = f.__doc__
    g.__dict__.update(f.__dict__)
    return g
  # Now a few lines needed to make simple_decorator itself
  # be a well-behaved decorator.
  new_decorator.__name__ = decorator.__name__
  new_decorator.__doc__ = decorator.__doc__
  new_decorator.__dict__.update(decorator.__dict__)
  return new_decorator

@decorator_shell
def check_serial_init(func):
  def x(*args, **kwargs):
    # args[0] == self
    if args[0]._s:
      return func(*args, **kwargs)
    else:
      raise NoSerial
  return x

CBMCOMMON = {
    "COMMAND" : 0x1B,
    "FULLCUT" : 0x69,
    "PARTIALCUT" : 0x6D,
    "LF" : 0x10,
    "LINEFEED_RATE" : 0x33,
    "PRINT_MODE" : 0x21,
    "DOUBLEPRINT" : 0x47,
    "UNDERLINE" : 0x2D,
    "RESET" : 0x40,
    "COMMAND_IMAGE" : 0x2A,
    "COMMAND_FLIPCHARS" : 0x7B,
    "COMMAND_ROTATECHARS" : 0x56,
    "COMMAND_BARCODE" : 0x1D,
    "COMMAND_BARCODE_PRINT" : 0x6B,
    "COMMAND_BARCODE_WIDTH" : 0x77,
    "COMMAND_BARCODE_HEIGHT" : 0x68,
    "COMMAND_BARCODE_TEXTPOSITION" : 0x48,
    "COMMAND_BARCODE_FONT" : 0x66
    }

CBMBARCODES = {
    "BARCODE_WIDTH_NARROW" : 0x02,
    "BARCODE_WIDTH_MEDIUM" : 0x03,
    "BARCODE_WIDTH_WIDE" : 0x04,
    "BARCODE_TEXT_NONE" : 0x00,
    "BARCODE_TEXT_ABOVE" : 0x01,
    "BARCODE_TEXT_BELOW" : 0x02,
    "BARCODE_TEXT_BOTH" : 0x03,
    "BARCODE_MODE_UPCA" : 0x00,
    "BARCODE_MODE_UPCE" : 0x01,
    "BARCODE_MODE_JAN13AEN" : 0x02,
    "BARCODE_MODE_JAN8EAN" : 0x03,
    "BARCODE_MODE_CODE39" : 0x04,
    "BARCODE_MODE_ITF" : 0x05,
    "BARCODE_MODE_CODEABAR" : 0x06,
    "BARCODE_MODE_CODE128" : 0x07
    }

CBM1000 = {}  # CBM1000 specific codes as necessary
CBM231 = {}  # CBM231 specific codes as necessary

def getMicroprinterCommands(model):
  commands = {}
  if model.lower().startswith("cbm"):
    commands.update(CBMCOMMON)
    commands.update(CBMBARCODES)
  if model.lower() == "cbm1000":
    commands.update(CBM1000)
  return commands

class Microprinter(object):
  def __init__(self, serialport, model="CBM"):
    self._s = None
    self.commands = {}
    self._serialport = serialport
    self.c = getMicroprinterCommands(model)
    self.reconnect()

  def reconnect(self):
    try:
      self._s = Serial(self._serialport, 9600)
    except Exception, e:
      logger.error("Couldn't open serial port %s" % self._serialport)
      logger.error(e)
    
  @check_serial_init
  def close(self):
    if self._s:
      self._s.close()

  @check_serial_init
  def sendcodes(self, *args):
    self._s.write("".join(map(chr, args)))

  @check_serial_init
  def write(self, *args):
    if len(args) == 1 and isinstance(args[0], basestring):
      logger.debug("Treating the 'write' argument as a string")
      logger.debug("Printing '%s'" % args[0])
      self._s.write(args[0])
    else:
      logger.debug("Treating the 'write' arguments as a list of strings")
      logger.debug("Printing '%s'" % "".join(args))
      self._s.write("".join(args))

  @check_serial_init
  def flush(self):
    self._s.flush()

  @check_serial_init
  def feed(self, lines=1):
    if lines and isinstance(lines, int):
      lines = lines % 256
      self.sendcodes(self.c['COMMAND'], 0x64, lines)
      self.flush()
    else:
      self.sendcodes(self.c['COMMAND'], 0x64, 1)
      self.flush()

  @check_serial_init
  def setPrintMode(self, mode):
    """Sets the printmode (0x1B 0x21 n == COMMAND PRINT_MODE mode)
    'mode' is a byte of flags:
    
    CBM1000
    bit 0 = font select - 0 - font A, 1 - font B
    bit 3 = 'Emphasis' (0/1 -> off/on)
    bit 4 = Double Height 
    bit 5 = Double width
    bit 7 = Underline
    
    see also the CBM1000Mode class
    """
    self.sendcodes(self.c['COMMAND'], self.c['PRINT_MODE'], mode)
    self.flush()
  
  @check_serial_init
  def printUPCABarcode(self, barcode):
    if 10 < len(barcode) < 13:
      logger.error("UPC-A barcodes must be between 11 and 12 'digits'")
      raise BarcodeException
    allowed = "0123456789"
    barcode = "".join([x for x in barcode if x in allowed])
    self.printBarcode(barcode, self.c['BARCODE_MODE_UPCA'])
  
  @check_serial_init
  def printBarcode(self, barcode, barcode_mode = None):
    if not barcode_mode:
      barcode_mode = self.c['BARCODE_MODE_UPCA']
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_PRINT'])
    self.sendcodes(barcode_mode)
    self.write(barcode)
    self.sendcodes(0x00) # NUL code

  @check_serial_init
  def setBarcodeDimensions(self, height=162, width=3):
    self.setBarcodeHeight(height)
    self.setBarcodeWidth(width)

  @check_serial_init
  def setBarcodeHeight(self, height=162):
    height = height % 256
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_HEIGHT'])
    self.sendcodes(height)
    self.flush()
  
  @check_serial_init
  def setBarcodeWidth(self, width=3):
    if (width < 2): width = 2
    if (width > 4): width = 4
    self.sendcodes(self.c['COMMAND_BARCODE'], self.c['COMMAND_BARCODE_WIDTH'])
    self.sendcodes(width)
    self.flush()
  
  @check_serial_init
  def resetState(self):
    self.sendcodes(self.c['COMMAND'], self.c['RESET'])
    self.flush()
  
  @check_serial_init
  def cut(self):
    self.sendcodes(self.c['COMMAND'], self.c['FULLCUT'])
  
  @check_serial_init
  def partialCut(self):
    self.sendcodes(self.c['COMMAND'], self.c['PARTIALCUT'])

  @check_serial_init
  def setDoubleprint(self, state=True):
    self.sendcodes(self.c['COMMAND'], self.c['DOUBLEPRINT'])
    if state:
      self.sendcodes(0x01)
    else:
      self.sendcodes(0x00)
    self.flush()

  @check_serial_init
  def setUnderline(self, state=True):
    self.sendcodes(self.c['COMMAND'], self.c['UNDERLINE'])
    if state:
      self.sendcodes(0x01)
    else:
      self.sendcodes(0x00)
    self.flush()
    
  @check_serial_init
  def formatting(self, commands):
    for command in commands:
      if command == "D":
        self.setDoubleprint(True)
      elif command == "d":
        self.setDoubleprint(False)
      elif command == "U":
        self.setUnderline(True)
      elif command == "u":
        self.setUnderline(False)

  @check_serial_init
  def printMarkup(self, markeduptext):
    def startFormatting(text, formatting = set()):
      if (text.startswith("*") and "D" not in formatting):
        formatting.add("D")
        text = text[1:]
        startFormatting(text, formatting)
      if (text.startswith("_") and "U" not in formatting):
        formatting.add("U")
        text = text[1:]
        startFormatting(text, formatting)
      return text, formatting
      
    def endFormatting(text, formatting = set()):
      if (text.endswith("*") and "d" not in formatting):
        formatting.add("d")
        text = text[:-1]
        startFormatting(text, formatting)
      if (text.endswith("_") and "u" not in formatting):
        formatting.add("u")
        text = text[:-1]
        startFormatting(text, formatting)
      return text, formatting
    
    for line in markeduptext.split("\n"):
      for token in line.split(" "):
        text, startcommands = startFormatting(token)
        text, endcommands = endFormatting(text)
        self.formatting(startcommands)
        self.write(text)
        self.formatting(endcommands)
        self.write(" ")
      self.feed()

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

  def print_imagebytes(self, m, data):
    self.sendcodes(self.c['COMMAND'], self.c['COMMAND_IMAGE'])
    density = 1
    if m == 1 or m == 33:
      density = 3
    datalength = len(data) / density
    self.sendcodes(m, datalength%256, datalength/256)
    self.sendcodes(*data)
    self.flush()

  def setLineFeedRate(self, feedlength):
    # <1B>H<33>H<n>
    self.sendcodes(self.c['COMMAND'], self.c['LINEFEED_RATE'])
    self.sendcodes(feedlength)
    self.flush()
  """
	void printSparkline(String label, int[] data) throws IOException { //works well with 255 bytes of data
		printer.write(label.substring(0, 7))
		printer.flush()
		fileout.write(COMMAND)
		fileout.write(COMMAND_IMAGE)
		fileout.write((byte) 0x0); 
		fileout.write((byte) 0x0); 
		fileout.write((byte) 0x01);		
		//convert the scale...
		int max = Integer.MIN_VALUE
		int min = Integer.MAX_VALUE
		for (int i = 0; i < data.length; i++) {
			if (data[i] > max) max = data[i]
			if (data[i] < min) min = data[i]
		}
		for (int i = 0; i < data.length; i++) {
			data[i] = (data[i] - min) * 7 / (max - min)
			int value = (int) Math.pow(2, data[i])
			fileout.write(value)
		}
	}

	void printDateBarcode() throws IOException {
		String dateStamp = new SimpleDateFormat("/yyyy/MM/dd/").format(new Date())
		setBarcodeHeight((byte) 50)
		setBarcodeWidth(BARCODE_WIDTH_MEDIUM)
		setBarcodeTextPosition(BARCODE_TEXT_BELOW)
		setBarcodeFont((byte) 0x01)
		printBarcode(dateStamp)
	}
"""

