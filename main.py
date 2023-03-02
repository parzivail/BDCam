#!/usr/bin/python3
import time
import json
import serial

import libcamera
from picamera2 import Picamera2
from picamera2.encoders import Encoder
from picamera2.outputs import FileOutput

class TrackingContext():
	def __init__(self, gps, nmeaFilename):
		self.gps = gps;
		self.nmeaFile = open(nmeaFilename, 'w')
		self.sentenceCount = 0

	def update(self):
		sentence = self.gps.readline().decode().rstrip()
		self.sentenceCount = self.sentenceCount + 1
		print(f"{self.sentenceCount},{sentence}", file=self.nmeaFile, flush=True)

	def get(self):
		return f"{self.sentenceCount}"
	
	def wait(self, seconds):
		start = time.time()
		while (time.time() - start < seconds):
			self.update()

class TrackedFileOutput(FileOutput):
	def __init__(self, context, file, pts):
		super().__init__(file, pts, None)
		self.context = context
		self.frameCounter = 0

	def outputtimestamp(self, timestamp):
		self.frameCounter = self.frameCounter + 1
		if self.ptsoutput is not None and timestamp is not None:
			print(f"{self.frameCounter},{timestamp},{self.context.get()}", file=self.ptsoutput, flush=True)

def hz_to_us(hz):
	return int(1000000 / hz)
	
gps = serial.Serial('/dev/ttyUSB0')

OUT_DIR = '/home/cnewman/bd1_share/local_data/'

FULL_SIZE = (4056, 3040) # About 10 FPS
HALF_SIZE = (2032, 1520) # About 40 FPS

CAM_RIGHT = 1
CAM_LEFT = 0

EXPOSURE = hz_to_us(500)
DURLIMIT = (hz_to_us(4), hz_to_us(4)) # 4 FPS

TRACKER = TrackingContext(gps, OUT_DIR + "nmea.txt")

outputFormat = {"format": 'SBGGR12', 'size': HALF_SIZE}
controls = {"FrameDurationLimits": DURLIMIT, "ExposureTime": EXPOSURE, "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off}
buffers = 4

metadata = {
	"output": outputFormat,
	"frame_limit": controls["FrameDurationLimits"],
	"exposure_time": controls["ExposureTime"]
}

with open(OUT_DIR + 'metadata.json', 'w', encoding='utf-8') as f:
  json.dump(metadata, f, ensure_ascii=False)

camLeft = Picamera2(CAM_LEFT)
camRight = Picamera2(CAM_RIGHT)

print("Configuring cameras")

cfgLeft = camLeft.create_video_configuration(raw=outputFormat, controls=controls, buffer_count=buffers)
cfgRight = camLeft.create_video_configuration(raw=outputFormat, controls=controls, buffer_count=buffers)

camLeft.configure(cfgLeft)
camRight.configure(cfgRight)

camLeft.encode_stream_name = "raw"
camRight.encode_stream_name = "raw"

outLeft = TrackedFileOutput(TRACKER, OUT_DIR + 'left.raw', pts=OUT_DIR + 'left.txt')
outRight = TrackedFileOutput(TRACKER, OUT_DIR + 'right.raw', pts=OUT_DIR + 'right.txt')

encoderLeft = Encoder()
encoderRight = Encoder()

print("Settling cameras")

TRACKER.wait(2)

print("Starting recording")

camLeft.start_recording(encoderLeft, outLeft)
camRight.start_recording(encoderRight, outRight)

# input("Waiting for keypress...")
# time.sleep(5)

TRACKER.wait(5)

print("Flushing recordings")
camLeft.stop_recording()
camRight.stop_recording()

print("Done")