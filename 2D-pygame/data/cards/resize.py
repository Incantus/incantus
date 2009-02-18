#!/usr/bin/python
import glob, os, shutil
from sets import Set as set

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

def resize_edition_old(edition, size):
    cards = file(edition+"/checklist.txt").readlines()
    cards = [c.strip().split("\t") for c in cards]
    cards = [[c[0], c[1]] for c in cards]
    w, h = size
    for id, name in cards:
        name = name.replace(" ", "_")
        #fname = "%03d_%s.jpg"%(int(id),name)
        fname = "%s_%s.jpg"%(id,name)
        resizeImagesQuartz(edition+"/full/"+fname, [(edition+"/small/"+fname, w, h)])

def resize_edition(edition, size, dest, done):
    path = "../../../../mtg_images"
    cards = file("%s/checklist.txt"%edition).readlines()
    cards = [c.strip().split("\t") for c in cards if c[0] != "#"]
    #fname = "%03d_%s.jpg"%(int(id),name)
    cards = ["%s_%s.jpg"%(id,name.replace(" ", "_")) for id,name in cards if name in done]

    w, h = size
    for fname in cards: resizeImagesQuartz("%s/%s/%s"%(path,edition,fname), [("./%s/%s/%s"%(edition,dest,fname), w, h)])

small_size = (65,93)
large_size = (234, 333)

editions = ["test", "8e", "9e", "10e", "lrw"]
for ed in editions:
    # Clear out old
    done = set([os.path.basename(d).replace("_", " ") for d in glob.glob("%s/obj/*"%ed)])
    for size, dest in [(large_size, "large"), (small_size, "small")]:
        path = "%s/%s"%(ed, dest)
        shutil.rmtree(path, True)
        os.mkdir(path)
        resize_edition(ed, size, dest, done)
