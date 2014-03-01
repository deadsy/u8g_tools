#! /usr/bin/python
#------------------------------------------------------------------------------
"""

Decode a u8g font from C code file of byte values

"""
#------------------------------------------------------------------------------

import getopt
import sys
import os

#------------------------------------------------------------------------------

_ifile = None
_ofile = None
_name = None

#------------------------------------------------------------------------------

def sex(x, n):
    """sign extend n-bit value x"""
    m = 1 << (n - 1)
    return (x ^ m) - m

#------------------------------------------------------------------------------

class glyph:
    def __init__(self, code, fmt, data, ofs):
        self.code = code
        self.fmt = fmt
        self.ofs = ofs # recorded for sanity checks
        if data[ofs] == 255:
            self.hdr_size = 1
            self.data_size = 0
        elif self.fmt in (0, 2):
            # 6 byte headers
            self.hdr_size = 6
            self.bb_width = data[ofs]
            self.bb_height = data[ofs + 1]
            self.data_size = data[ofs + 2]
            self.dwidth = sex(data[ofs + 3], 8)
            self.bb_xofs = sex(data[ofs + 4], 8)
            self.bb_yofs = sex(data[ofs + 5], 8)
        else:
            # 3 byte headers
            self.hdr_size = 3
            x = data[ofs]
            self.bb_xofs = sex(x >> 4, 4)
            self.bb_yofs = sex(x & 15, 4)
            x = data[ofs + 1]
            self.bb_width = x >> 4
            self.bb_height = x & 15
            x = data[ofs + 2]
            self.data_size = x & 15
            self.dwidth = sex(x >> 4, 4)
        self.data = data[ofs + self.hdr_size: ofs + self.hdr_size + self.data_size]
        # sanity checks
        if self.hdr_size != 1:
            assert self.data_size == self.bb_height * ((self.bb_width + 7) >> 3)

    def size(self):
        return self.hdr_size + self.data_size

    def bitmap(self):
        """return a string of the bitmap"""
        if self.hdr_size == 1:
            return None
        s = []
        ofs = 0
        bytes_per_line = (self.bb_width + 7) >> 3
        for row in range(self.bb_height):
            row = []
            if bytes_per_line == 1:
                row_data = self.data[ofs]
                ofs += 1
                mask = (1 << 7)
            elif bytes_per_line == 2:
                row_data = (self.data[ofs] << 8) + self.data[ofs + 1];
                ofs += 2
                mask = (1 << 15)
            else:
                assert False
            for col in range(self.bb_width):
                row.append(('.', '*')[row_data & mask != 0])
                mask >>= 1
            s.append(''.join(row))
        return '\n'.join(s)

    def __str__(self):
        s = []
        s.append('    0x%02x:' % self.code)
        if self.hdr_size == 1:
            s.append(' None,')
        else:
            s.append(' (%d,%d,' % (self.bb_width, self.bb_height))
            s.append('%d,%d,' % (self.bb_xofs, self.bb_yofs))
            s.append('%d,' % (self.dwidth))
            if self.data_size:
                s.append('(%s,)),' % ','.join(['0x%02x' % x for x in self.data]))
            else:
                s.append('None),')
        if self.code >= 0x20 and self.code <= 0x7e:
            s.append(' # \'%c\'' % chr(self.code))
        return ''.join(s)

#------------------------------------------------------------------------------

_FONT_HDR_SIZE = 17

class font:
    def __init__(self, name):
        self.name = name

    def read_from_file(self, fname):
        f = open(fname)
        data = f.read()
        f.close()
        data = data.split('{')[1]
        data = data.split('}')[0]
        data = data.split(',')
        self.data = [int(x.strip()) for x in data]

    def write_py_file(self, fname):
        f = open(fname, 'w')
        f.write(str(self))
        f.close()

    def __str__(self):
        s = []
        # output glyphs
        s.append('#  %s\n' % self.name)
        s.append('glyphs = {')
        s.append('    # code: (width, height, xofs, yofs, dwidth, data)')
        for g in self.glyphs:
            s.append(str(g))
        s.append('}')
        # output font header info
        s.append('font = {')
        s.append('    \'%s\': \'%s\',' % ('name', self.name))
        s.append('    \'%s\': %s,' % ('glyphs', 'glyphs'))
        s.append('    \'%s\': %d,' % ('fmt', self.fmt))
        s.append('    \'%s\': %d,' % ('bb_width', self.bb_width))
        s.append('    \'%s\': %d,' % ('bb_height', self.bb_height))
        s.append('    \'%s\': %d,' % ('bb_xofs', self.bb_xofs))
        s.append('    \'%s\': %d,' % ('bb_yofs', self.bb_yofs))
        s.append('    \'%s\': %d,' % ('capital_a_height', self.capital_a_height))
        s.append('    \'%s\': %d,' % ('code_65_ofs', self.code_65_ofs))
        s.append('    \'%s\': %d,' % ('code_97_ofs', self.code_97_ofs))
        s.append('    \'%s\': 0x%02x,' % ('start_code', self.start_code))
        s.append('    \'%s\': 0x%02x,' % ('end_code', self.end_code))
        s.append('    \'%s\': %d,' % ('lower_g_descent', self.lower_g_descent))
        s.append('    \'%s\': %d,' % ('font_ascent', self.font_ascent))
        s.append('    \'%s\': %d,' % ('font_descent', self.font_descent))
        s.append('    \'%s\': %d,' % ('font_x_ascent', self.font_x_ascent))
        s.append('    \'%s\': %d,' % ('font_x_descent', self.font_x_descent))
        s.append('}')
        return '\n'.join(s)

    def decode_header(self):
        self.fmt = self.data[0]
        self.start_code = self.data[10]
        self.end_code = self.data[11]
        self.code_65_ofs = (self.data[6] << 8) + self.data[7]
        self.code_97_ofs = (self.data[8] << 8) + self.data[9]
        self.bb_width = self.data[1]
        self.bb_height = self.data[2]
        self.bb_xofs = self.data[3]
        self.bb_yofs = sex(self.data[4], 8)
        self.capital_a_height = self.data[5]
        self.lower_g_descent= sex(self.data[12], 8)
        self.font_ascent = sex(self.data[13], 8)
        self.font_descent = sex(self.data[14], 8)
        self.font_x_ascent = sex(self.data[15], 8)
        self.font_x_descent = sex(self.data[16], 8)

    def get_glyph(self, code):
        if code < self.start_code or code > self.end_code:
            return None
        return self.glyphs[code - self.start_code]

    def decode_glyphs(self):
        self.glyphs = []
        code = self.start_code
        ofs = _FONT_HDR_SIZE
        while ofs < len(self.data):
            g = glyph(code, self.fmt, self.data, ofs)
            self.glyphs.append(g)
            code += 1
            ofs += g.size()
        # sanity checks
        assert ofs == len(self.data)
        assert self.end_code == (code - 1)
        if self.code_65_ofs:
            assert self.get_glyph(65).ofs == self.code_65_ofs
        if self.code_97_ofs:
            assert self.get_glyph(97).ofs == self.code_97_ofs

    def decode(self):
        self.decode_header()
        self.decode_glyphs()

#------------------------------------------------------------------------------

def print_usage(argv):
    print 'Usage: %s [options]' % argv[0]
    print 'Options:'
    print '%-18s%s' % ('-i <input_file>', 'input file')
    print '%-18s%s' % ('-o <output_file>', 'output file')
    print '%-18s%s' % ('-n <font_name>', 'font name')

def error(msg, usage = False):
    print 'error: %s' % msg
    if usage:
        print_usage(sys.argv)
    sys.exit(1)

def process_options(argv):
    """process command line options"""
    global _ifile, _ofile, _name
    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "i:o:n:")
    except getopt.GetoptError, err:
        error(str(err), True)
    if args:
        error('invalid arguments on command line', True)
    for (opt, val) in opts:
        if opt == '-i':
            _ifile = val
        if opt == '-o':
            _ofile = val
        if opt == '-n':
            _name = val

    if not _ifile:
        error('specify an input file', True)

    if not _name:
        _name =  os.path.split(_ifile)[1].split('.')[0]

    if not _ofile:
        _ofile =  '%s/%s.py' % (os.path.split(_ifile)[0], _name)

#------------------------------------------------------------------------------

def main():
    process_options(sys.argv)
    f = font(_name)
    f.read_from_file(_ifile)
    f.decode()
    f.write_py_file(_ofile)

main()

#------------------------------------------------------------------------------
