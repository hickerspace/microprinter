import sys, os
import Image

from microprinter import Microprinter

from microprinter_image import print_image

if len(sys.argv) < 4:
    print "Usage: ./print_image_hires.py {ArduinoSerialport} {paper width} {path/to/image} {path/to/image} etc"
    print "paper width (in mm) - eg 57, 58 or 80"
    print "Example: ./print_image_hires.py /dev/ttyUSB0 58 /home/ben/image.png"
    sys.exit(1)


m = Microprinter(sys.argv[1])
width = int(sys.argv[2])

if 55 < width <59:
    width = 432
elif width == 80:
    width = 576

mode = 33

for infile in sys.argv[3:]:
    try:
        im = Image.open(infile)
        print "Sending %s to the printer" % infile
        print_image(im, width, mode, m)
        m.feed()
        m.feed(5)
        m.cut()
    except IOError:
        pass

