#! /usr/bin/python3
#------------------------------------------------------------------------------
"""

Take a font defined as python data structures - encode it as a u8g font

"""
#------------------------------------------------------------------------------

import getopt
import sys
import os

#------------------------------------------------------------------------------

_ifile = None
_ofile = None

#------------------------------------------------------------------------------

def print_usage(argv):
  print('Usage: %s [options]' % argv[0])
  print('Options:')
  print('%-18s%s' % ('-i <input_file>', 'input file'))
  print('%-18s%s' % ('-o <output_file>', 'output file'))

def error(msg, usage=False):
  print('error: %s' % msg)
  if usage:
    print_usage(sys.argv)
  sys.exit(1)

def warning(msg, fname=True):
  if fname:
    print('%s: warning: %s' % (_ifile, msg))
  else:
    print('warning: %s' % msg)

def process_options(argv):
  """process command line options"""
  global _ifile, _ofile, _name
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], "i:o:")
  except getopt.GetoptError as err:
    error(str(err), True)
  if args:
    error('invalid arguments on command line', True)
  for (opt, val) in opts:
    if opt == '-i':
      _ifile = val
    if opt == '-o':
      _ofile = val

  if not _ifile:
    error('specify an input file', True)

  if not _ofile:
    name = os.path.split(_ifile)[1].split('.')[0]
    _ofile = '%s/%s.c' % (os.path.split(_ifile)[0], name)

#------------------------------------------------------------------------------

_FONT_HDR_SIZE = 17

class font:
  def __init__(self, d):
    self.glyphs = {}
    self.__dict__.update(d)

  def write_c_file(self, fname):
    f = open(fname, 'w')
    f.write(str(self))
    f.close()

  def encode_header(self):
    d = []
    d.append(self.fmt) # 0
    d.append(self.bb_width) # 1
    d.append(self.bb_height) # 2
    d.append(self.bb_xofs) # 3
    d.append(self.bb_yofs & 255) # 4
    d.append(self.capital_a_height) # 5
    d.append(self.code_65_ofs >> 8) # 6
    d.append(self.code_65_ofs & 255) # 7
    d.append(self.code_97_ofs >> 8) # 8
    d.append(self.code_97_ofs & 255) # 9
    d.append(self.start_code) # 10
    d.append(self.end_code) # 11
    d.append(self.lower_g_descent & 255) # 12
    d.append(self.font_ascent & 255) # 13
    d.append(self.font_descent & 255) # 14
    d.append(self.font_x_ascent & 255) # 15
    d.append(self.font_x_descent & 255) # 16
    return d

  def encode_glyph(self, code):
    d = []
    if (not code in self.glyphs) or (self.glyphs[code] is None):
      # no data for this glyph
      d.append(255)
    else:
      (bb_width, bb_height, bb_xofs, bb_yofs, dwidth, data) = self.glyphs[code]
      # emit the glyph data
      if self.fmt in (0, 2):
        # 6 byte headers
        d.append(bb_width) # 0
        d.append(bb_height) # 1
        if data:
          d.append(len(data)) # 2
        else:
          d.append(0) # 2
        d.append(dwidth & 255) # 3
        d.append(bb_xofs & 255) # 4
        d.append(bb_yofs & 255) # 5
      else:
        # 3 byte headers
        x = (bb_xofs & 15) << 4
        x |= (bb_yofs & 15)
        d.append(x) # 0
        x = (bb_width & 15) << 4
        x |= (bb_height & 15)
        d.append(x) # 1
        x = (dwidth & 15) << 4
        if data:
          x |= len(data) & 15
        d.append(x) # 2
      if data:
        d.extend(list(data))
    return d

  def calc_start_code(self):
    """work out the start code"""
    sc = 0xff
    for code in self.glyphs.keys():
      if code < sc:
        sc = code
    return sc

  def calc_end_code(self):
    """work out the end code"""
    ec = 0
    for code in self.glyphs.keys():
      if code > ec:
        ec = code
    return ec

  def glyph_ascent(self, code):
    """return the ascent of the glyph"""
    if code in self.glyphs and self.glyphs[code]:
      (width, height, xofs, yofs, dwidth, data) = self.glyphs[code]
      return height + yofs
    return 0

  def glyph_descent(self, code):
    """return the descent of the glyph"""
    if code in self.glyphs and self.glyphs[code]:
      (width, height, xofs, yofs, dwidth, data) = self.glyphs[code]
      return yofs
    return 0

  def calc_capital_a_height(self):
    """Ascent will be the ascent of "A" or "1" of the current font"""
    return max(self.glyph_ascent(ord('A')), self.glyph_ascent(ord('1')))

  def calc_lower_g_descent(self):
    """Descent will be the descent "g" of the current font"""
    return self.glyph_descent(ord('g'))

  def calc_font_x_ascent(self):
    """Ascent will be the largest ascent of "A", "1" or "(" of the current font"""
    return max(self.glyph_ascent(ord('A')), self.glyph_ascent(ord('1')), self.glyph_ascent(ord('(')))

  def calc_font_x_descent(self):
    """Descent will be the descent of "g" or "(" of the current font"""
    return min(self.glyph_descent(ord('g')), self.glyph_descent(ord('(')))

  def calc_font_ascent(self):
    """Ascent will be the highest ascent of all glyphs of the current font"""
    return max([self.glyph_ascent(code) for code in self.glyphs.keys()])

  def calc_font_descent(self):
    """Descent will be the highest descent of all glyphs of the current font"""
    return min([self.glyph_descent(code) for code in self.glyphs.keys()])

  def __str__(self):

    if not hasattr(self, 'name'):
      self.name = 'u8g_font'

    if not hasattr(self, 'glyphs'):
      error('no glyphs defined')

    if hasattr(self, 'start_code'):
      if self.start_code != self.calc_start_code():
        error('start_code is not the lowest glyph code')
    else:
      self.start_code = self.calc_start_code()

    if hasattr(self, 'end_code'):
      if self.end_code != self.calc_end_code():
        error('end_code is not the highest glyph code')
    else:
      self.end_code = self.calc_end_code()

    if hasattr(self, 'capital_a_height'):
      if self.capital_a_height != self.calc_capital_a_height():
        warning('capital_a_height does match glyphs')
    else:
      self.capital_a_height = self.calc_capital_a_height()

    if hasattr(self, 'lower_g_descent'):
      if self.lower_g_descent != self.calc_lower_g_descent():
        warning('lower_g_descent does match glyphs')
    else:
      self.lower_g_descent = self.calc_lower_g_descent()

    if hasattr(self, 'font_x_ascent'):
      if self.font_x_ascent != self.calc_font_x_ascent():
        warning('font_x_ascent does match glyphs')
    else:
      self.font_x_ascent = self.calc_font_x_ascent()

    if hasattr(self, 'font_x_descent'):
      if self.font_x_descent != self.calc_font_x_descent():
        warning('font_x_descent does match glyphs')
    else:
      self.font_x_descent = self.calc_font_x_descent()

    if hasattr(self, 'font_ascent'):
      if self.font_ascent != self.calc_font_ascent():
        warning('font_ascent does match glyphs')
    else:
      self.font_ascent = self.calc_font_ascent()

    if hasattr(self, 'font_descent'):
      if self.font_descent != self.calc_font_descent():
        warning('font_descent does match glyphs')
    else:
      self.font_descent = self.calc_font_descent()

    if not hasattr(self, 'fmt'):
      self.fmt = 0
    if not hasattr(self, 'bb_width'):
      self.bb_width = 0
    if not hasattr(self, 'bb_height'):
      self.bb_height = 0
    if not hasattr(self, 'bb_xofs'):
      self.bb_xofs = 0
    if not hasattr(self, 'bb_yofs'):
      self.bb_yofs = 0

    glyph_data = []
    for code in range(self.start_code, self.end_code + 1):
      # work out the 'A' offset
      if code == ord('A'):
        if hasattr(self, 'code_65_ofs'):
          if self.code_65_ofs != _FONT_HDR_SIZE + len(glyph_data):
            error('code_65_ofs mismatch')
        else:
          self.code_65_ofs = _FONT_HDR_SIZE + len(glyph_data)
    # work out the 'a' offset
      if code == ord('a'):
        if hasattr(self, 'code_97_ofs'):
          if self.code_97_ofs != _FONT_HDR_SIZE + len(glyph_data):
            error('code_97_ofs mismatch')
        else:
          self.code_97_ofs = _FONT_HDR_SIZE + len(glyph_data)
      # encode the glyph
      glyph_data.extend(self.encode_glyph(code))

    data = self.encode_header()
    data.extend(glyph_data)

    n = len(data)
    s = []
    s.append('const u8g_fntpgm_uint8_t %s[%d] U8G_FONT_SECTION("%s") = {\n' % (self.name, n, self.name))
    i = 0
    while n > 0:
      s.append('  ')
      k = (n, 16)[n > 16]
      ls = []
      for j in range(k):
        ls.append('%d' % data[i])
        i += 1
      s.append(','.join(ls))
      if k == 16:
        s.append(',\n')
      n -= k
    s.append('};')
    return ''.join(s)

#------------------------------------------------------------------------------

def main():
  process_options(sys.argv)
  import_dir = os.path.split(_ifile)[0]
  import_name = os.path.split(_ifile)[1].split('.')[0]
  sys.path.append(import_dir)
  module = __import__(import_name)
  f = font(module.font)
  f.write_c_file(_ofile)

main()

#------------------------------------------------------------------------------
