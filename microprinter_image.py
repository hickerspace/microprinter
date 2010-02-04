import sys, os
import Image

from microprinter import Microprinter

from time import sleep

def print_row(data, mode, m):
  bytes = []
  if mode < 2:
    for x in range(len(data[0])):
      byte_column = data[0][x] << 7|data[1][x] << 6|data[2][x] << 5|data[3][x] << 4|data[4][x] << 3|data[5][x] << 2|data[6][x] << 1|data[7][x]
      bytes.append(byte_column ^ 255)
  else:
    for x in range(len(data[0])):
      byte_column = data[0][x] << 7|data[1][x] << 6|data[2][x] << 5|data[3][x] << 4|data[4][x] << 3|data[5][x] << 2|data[6][x] << 1|data[7][x]
      bytes.append(byte_column ^ 255)
      byte_column = data[8][x] << 7|data[9][x] << 6|data[10][x] << 5|data[11][x] << 4|data[12][x] << 3|data[13][x] << 2|data[14][x] << 1|data[15][x]
      bytes.append(byte_column ^ 255)
      byte_column = data[16][x] << 7|data[17][x] << 6|data[18][x] << 5|data[19][x] << 4|data[20][x] << 3|data[21][x] << 2|data[22][x] << 1|data[23][x]
      bytes.append(byte_column ^ 255)
  m.print_imagebytes(mode, bytes)

def print_image(im, width, mode, m, autorotate=True):
  m.setLineFeedRate(1)
  rowlimit = 8
  fudgefactor = 0.66
  if mode > 1:
    rowlimit = 24
    fudgefactor = 1.0
  im = im.convert("1", dither = Image.FLOYDSTEINBERG)
  size = im.size
  if autorotate:
    if size[0] > size[1]:
      # Landscape ratio
      im = im.transpose(Image.ROTATE_90)
  resize_ratio = (float(width)/im.size[0])*fudgefactor #  fudge factor for scaling
  im = im.resize((width, int(resize_ratio * im.size[1])))
  lbuffer = []
  rows = 0
  columns = 0
  cbuffer = []
  for pixel in im.getdata():
    columns = columns + 1
    if pixel > 128:
      cbuffer.append(1)
    else:
      cbuffer.append(0)
    if columns == width:
      lbuffer.append(cbuffer)
      cbuffer = []
      columns = 0
      if len(lbuffer) == rowlimit:
        print_row(lbuffer, mode, m)
        sleep(0.2)
        lbuffer = []
        rows = rows + 1
  if 0 < len(lbuffer) < 8:
    lbuffer.extend([[1]*width]*(rowlimit-len(lbuffer)))
    print_row(lbuffer, mode, m)
    sleep(0.2)
  m.resetState()

