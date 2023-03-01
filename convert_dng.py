#!/usr/bin/python3
import time

import numpy as np
from pidng.core import RAW2DNG, DNGTags, Tag
from pidng.defs import *
from PIL import Image

size = (2032, 1520)

buf = open("/home/cnewman/bd1_share/local_data/left.raw", "rb").read(size[0] * size[1] * 2)
arr = np.frombuffer(buf, dtype=np.uint16).reshape((size[1], size[0]))

# uncalibrated color matrix, just for demo. 
ccm1 = [[19549, 10000], [-7877, 10000], [-2582, 10000],	
        [-5724, 10000], [10121, 10000], [1917, 10000],
        [-1267, 10000], [ -110, 10000], [ 6621, 10000]]

# Create DNG file from frame, based on https://github.com/schoolpost/PiDNG/blob/master/examples/raw2dng.py
# Tested loading of DNG in darktable
r = RAW2DNG()
t = DNGTags()
bpp = 12

profile_name = "Repro 2_5D no LUT - D65 is really 5960K"
profile_embed = 3

ccm1 = [[6759, 10000], [-2379, 10000], [751, 10000],
		[-4432, 10000], [13871, 10000], [5465, 10000],
		[-401, 10000], [1664, 10000], [7845, 10000]]

ccm2 = [[5603, 10000], [-1351, 10000], [-600, 10000],
		[-2872, 10000], [11180, 10000], [2132, 10000],
		[600, 10000], [453, 10000], [5821, 10000]]

fm1 = [[7889, 10000], [1273, 10000], [482, 10000],
		[2401, 10000], [9705, 10000], [-2106, 10000],
		[-26, 10000], [-4406, 10000], [12683, 10000]]

fm2 = [[6591, 10000], [3034, 10000], [18, 10000],
		[1991, 10000], [10585, 10000], [-2575, 10000],
		[-493, 10000], [-919, 10000], [9663, 10000]]

camera_calibration = [[1, 1], [0, 1], [0, 1],
						[0, 1], [1, 1], [0, 1],
						[0, 1], [0, 1], [1, 1]]

gain_r = 2500
gain_b = 2000

as_shot_neutral = [[1000, gain_r], [1000, 1000], [1000, gain_b]]

ci1 = CalibrationIlluminant.Standard_Light_A
ci2 = CalibrationIlluminant.D65

width = size[0]
height = size[1]
baseline_exp = 1

t.set(Tag.ImageWidth, width)
t.set(Tag.ImageLength, height)
t.set(Tag.TileWidth, width)
t.set(Tag.TileLength, height)
t.set(Tag.Orientation, Orientation.Horizontal)
t.set(Tag.PhotometricInterpretation, PhotometricInterpretation.Color_Filter_Array)
t.set(Tag.SamplesPerPixel, 1)
t.set(Tag.BitsPerSample, bpp)
t.set(Tag.CFARepeatPatternDim, [2,2])
t.set(Tag.CFAPattern, CFAPattern.BGGR)
t.set(Tag.BlackLevel, (4096 >> (16 - bpp)))
t.set(Tag.WhiteLevel, ((1 << bpp) -1) )
t.set(Tag.ColorMatrix1, ccm1)
t.set(Tag.ColorMatrix2, ccm2)
t.set(Tag.ForwardMatrix1, fm1)
t.set(Tag.ForwardMatrix2, fm2)
t.set(Tag.CameraCalibration1, camera_calibration)
t.set(Tag.CameraCalibration2, camera_calibration)
t.set(Tag.CalibrationIlluminant1, ci1)
t.set(Tag.CalibrationIlluminant2, ci2)
t.set(Tag.BaselineExposure, [[baseline_exp,1]])
t.set(Tag.AsShotNeutral, as_shot_neutral)
t.set(Tag.ProfileName, profile_name)
t.set(Tag.ProfileEmbedPolicy, [profile_embed])
t.set(Tag.DNGVersion, DNGVersion.V1_4)
t.set(Tag.DNGBackwardVersion, DNGVersion.V1_2)
r.options(t, path="", compress=False)
r.convert(arr, filename="test")