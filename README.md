
The u8g library encodes fonts as C arrays of byte values.
To make it easier to manipulate the fonts these tools can:
a) decode them into readable python code
b) re-encode them as C arrays.

font_decode.py : font.c -> font.py
font_encode.py : font.py -> font.c
./fonts : Some fonts in *.py form
