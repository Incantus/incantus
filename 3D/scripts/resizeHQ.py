#!/usr/bin/python

def resizeImagesQuartz(origFilename, newImagesInfo):
    # newImagesInfo is a list of
    # (newFilename, newWidth, newHeight) tuples
    if not newImagesInfo: return
    import CoreGraphics
    origImage = CoreGraphics.CGImageCreateWithJPEGDataProvider(
        CoreGraphics.CGDataProviderCreateWithFilename(origFilename),
        [0,1,0,1,0,1], 1, CoreGraphics.kCGRenderingIntentDefault)
    for newFilename, newWidth, newHeight in newImagesInfo:
        print "Resizing image with Quartz: ", newFilename, newWidth, newHeight
        cs = CoreGraphics.CGColorSpaceCreateDeviceRGB()
        c = CoreGraphics.CGBitmapContextCreateWithColor(newWidth, newHeight, cs, (0,0,0,0))
        c.setInterpolationQuality(CoreGraphics.kCGInterpolationHigh)
        newRect = CoreGraphics.CGRectMake(0, 0, newWidth, newHeight)
        c.drawImage(newRect, origImage)
        c.writeToFile(newFilename, CoreGraphics.kCGImageFormatJPEG)
            # final params parameter?

import glob, os
def resize_edition(size, dest):
    cardfiles = glob.glob("full/*.jpg")
    names = [os.path.basename(c).split('.')[0] for c in cardfiles]
    w, h = size
    for name, fname in zip(names, cardfiles):
        resize_name = name+".jpg"
        resizeImagesQuartz(fname, [(resize_name, w, h)])

large_size = (200, 285)
large_size = (208, 296)
resize_edition(large_size, "db")
