#! /usr/bin/python
#------------------------------------------------------------------------------
"""

Take a font defined as python data structures - encode it as a u8g font

"""

#------------------------------------------------------------------------------

_FONT_HDR_SIZE = 17

class font:
    def __init__(self, d):
        self.__dict__.update(d)
        self.start_code = 0xffff
        self.end_code = 0
        self.code_65_ofs = 0
        self.code_97_ofs = 0
        self.capital_a_height = 0

    def write_c_file(self):
        f = open('%s.c' % self.name, 'w')
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

    def encode_glyphs(self):
        d = []
        for g in self.glyphs:

            # work out the start and end codes
            code = g[0]
            if code < self.start_code:
                self.start_code = code
            if code > self.end_code:
                self.end_code = code

            # check for 'A' and 'a' offsets
            if code == ord('A'):
                self.code_65_ofs = len(d) + _FONT_HDR_SIZE
            if code == ord('a'):
                self.code_97_ofs = len(d) + _FONT_HDR_SIZE

            # check for no glyph data
            if g[1] is None:
                # no data for this glyph
                d.append(255)
                continue

            (code, bb_width, bb_height, bb_xofs, bb_yofs, dwidth, data) = g

            # get capital 'A' height
            if code == ord('A'):
                self.capital_a_height = bb_height

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

    def __str__(self):

        glyph_data = self.encode_glyphs()
        data = self.encode_header()
        data.extend(glyph_data)

        n = len(data)
        s = []
        s.append('const u8g_fntpgm_uint8_t %s[%d] U8G_FONT_SECTION("%s") = {\n' % (self.name, n, self.name))
        i = 0
        while n > 0:
            s.append('    ')
            k = (n, 16)[n > 16]
            for j in range(k):
                s.append('%d,' % data[i])
                i += 1
            s.append('\n')
            n -= k
        s.append('};\n')
        return ''.join(s)

#------------------------------------------------------------------------------

def main():
    #name = 'u8g_font_04b_03b'
    #name = 'u8g_font_04b_03bn'
    #name = 'u8g_font_tpssr'
    #name = 'u8g_font_unifont'
    name = 'nokia_large'
    module = __import__(name)
    f = font(module.font)
    f.write_c_file()

main()

#------------------------------------------------------------------------------

