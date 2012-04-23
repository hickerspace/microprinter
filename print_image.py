#!/usr/bin/env python

import sys, os
import Image

from microprinter import Microprinter

from microprinter_image import print_image

if len(sys.argv) < 5:
    print "Usage: ./print_image.py {ArduinoSerialport} {width} {mode} {path/to/image} {path/to/image} etc"
    print "width - the print width of the image in pixels (57mm paper - 216px lowres or 432px highres)"
    print "mode - 0 - 101dpi x 67dpi resolution"
    print "mode - 1 - 203dpi x 67dpi resolution"
    print "mode - 32 - 101dpi x 203dpi resolution"
    print "mode - 33 - 203dpi x 203dpi resolution"
    print "Example: ./print_image_hires.py /dev/ttyUSB0 432 33 /home/ben/image.png"
    sys.exit(1)
    

m = Microprinter(sys.argv[1], "CBM1000")
width = int(sys.argv[2])
mode = int(sys.argv[3])

for infile in sys.argv[4:]:
    try:
        im = Image.open(infile)
        print "Sending %s to the printer" % infile
        print_image(im, width, mode, m)
        m.feed()
        m.feed(5)
        m.cut()
    except IOError:
        pass

