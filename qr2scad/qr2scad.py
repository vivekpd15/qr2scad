#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""qr2scad - Convert QR code images to OpenSCAD
<http://github.com/l0b0/qr2scad>

Default syntax:

qr2scad < input_file

Description:

For each black pixel in the input, it will create a cube in the output.

The result can be used in an existing OpenSCAD file as follows:
1. Remove the QR code from a flat surface using the difference() function.
2. After printing, splash some removable paint or ink on the QR code holes.
3. Remove the residue around the holes with a piece of cloth, leaving the color
in the holes intact.

Examples:

qr2scad < example.png > example.scad
    Convert example.png to example.scad

<http://www.thingiverse.com/thing:4448>

Bugs: <https://github.com/l0b0/qr2scad/issues>
"""

from PIL import Image, ImageOps
from signal import signal, SIGPIPE, SIG_DFL
import qrcode as qrc
import argparse
import sys

BLOCK_SIZE = 1
"""<http://www.denso-wave.com/qrcode/qrgene3-e.html> recommends at least four
dots per module, so with a 0.1mm accuracy you should use at least 0.4 +
BLOCK_PADDING.
"""

BLOCK_PADDING = 0.01
"""Cubes have to be less than 1 unit wide. Otherwise you will get the message
Object isn't a valid 2-manifold! on STL export (see
<http://en.wikibooks.org/wiki/OpenSCAD_User_Manual/STL_Import_and_Export>)."""

BLOCK_SIDE = BLOCK_SIZE - BLOCK_PADDING
"""This is the actual side length of a block."""

PDP_SIDE = 7
"""The position detection patterns (PDPs) are 7x7 pixels."""

signal(SIGPIPE, SIG_DFL)
"""Avoid 'Broken pipe' message when canceling piped command."""


def qr2scad(infile,outfile,render=False):
    """Convert black pixels to OpenSCAD cubes."""
    img = Image.open(infile)

    # Convert to black and white 8-bit
    if img.mode != 'L':
        img = img.convert('L')

    # Invert color to get the right bounding box
    img = ImageOps.invert(img)

    bbox = img.getbbox()

    # Crop to only contain contents within the PDPs
    img = img.crop(bbox)

    width, height = img.size

    assert width == height,\
        'The QR code should be a square, but we found it to be %(w)sx%(h)s' % {
            'w': width,
            'h': height
        }

    qr_side = width

    # QR code superpixel size
    qr_pixel_size = (list(img.getdata()).index(0) / PDP_SIDE)

    # Get the resize factor from the PDP size
    new_size = qr_side / qr_pixel_size

    # Set a more reasonable size
    img = img.resize((new_size, new_size))
    qr_side = new_size

    img_matrix = img.load()

    result = 'module _qr_code_dot() {\n'
    result += '    cube([%(block_side)s, %(block_side)s, 1]);\n' % {
        'block_side': BLOCK_SIDE
    }
    result += '}\n'

    result += 'module qr_code() {\n'
    for row in range(qr_side):
        for column in range(qr_side):
            if img_matrix[column, row] != 0:
                result += '    translate([%(x)s, %(y)s, 0])' % {
                    'x': BLOCK_SIZE * column - qr_side / 2,
                    'y': -BLOCK_SIZE * row + qr_side / 2
                }
                result += ' _qr_code_dot();\n'
    result += '}\n'
    result += 'qr_code_size = %d;' % (qr_side)
    if( render ):
        result += "\nqr_code();"
    f = open(outfile,"w+")
    f.write(result)
    f.close()
    return result


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Input png file.")
    parser.add_argument("outfile", help="Output scad file")
    parser.add_argument("-v", "--verbosity", action="count",
                        help="write to screen")
    parser.add_argument("-r", "--render", action="count",
                        help="Have the scad render the qr code.")
    parser.add_argument("-g", "--generate",  
                        help="generate")
    args = parser.parse_args()
#    if( args.help ):
#        print 'python qr2scad -r <qrcodefile.png> <outfile.scad> -g <string you want to generate e.g. "Hi Mom".>'

    if(args.generate):
        qr = qrc.QRCode(
            version=1,
            error_correction=qrc.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
            )
        qr.add_data(args.generate)
        qr.make(fit=True)
        img = qr.make_image()
        img.save(args.infile)
        print "Generating QR Code for <{0}>. Saving it to {1}.".format( args.generate,args.infile) 
        
    print "Using {0} to generate {1}.".format(args.infile,args.outfile)
    result = qr2scad(args.infile,args.outfile,args.render)
    if(args.verbosity):
        print result

    
if __name__ == '__main__':
    sys.exit(main())
