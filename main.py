import time
import signal
import subprocess
import prctl
import json

import libcamera
import picamera2.formats as formats
from picamera2 import Picamera2
from picamera2.encoders import Encoder, H264Encoder
from picamera2.outputs import Output

def hz_to_us(hz):
	return int(1000000 / hz)

OUT_DIR = '/home/cnewman/bd1_share/local_data/'

FULL_SIZE = (4056, 3040) # About 10 FPS
HALF_SIZE = (2032, 1520) # About 40 FPS

CAM_RIGHT = 1
CAM_LEFT = 0

EXPOSURE = hz_to_us(500)
DURLIMIT = (hz_to_us(4), hz_to_us(4)) # 4 FPS

outputFormat = {"format": 'SBGGR12', 'size': HALF_SIZE}
controls = {"FrameDurationLimits": DURLIMIT, "ExposureTime": EXPOSURE, "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off}
buffers = 4

metadata = {
	"output": outputFormat,
	"frame_limit": controls["FrameDurationLimits"],
	"exposure_time": controls["ExposureTime"]
}

camLeft = Picamera2(CAM_LEFT)
camRight = Picamera2(CAM_RIGHT)

print("Configuring cameras")

with open(OUT_DIR + 'metadata.json', 'w', encoding='utf-8') as f:
  json.dump(metadata, f, ensure_ascii=False)

cfgLeft = camLeft.create_video_configuration(raw=outputFormat, controls=controls, buffer_count=buffers)
cfgRight = camLeft.create_video_configuration(raw=outputFormat, controls=controls, buffer_count=buffers)

camLeft.configure(cfgLeft)
camRight.configure(cfgRight)

camLeft.encode_stream_name = "raw"
camRight.encode_stream_name = "raw"

encoderLeft = Encoder()
encoderRight = Encoder()

print("Settling cameras")

time.sleep(2)

print("Starting recording")

camLeft.start_recording(encoderLeft, OUT_DIR + 'left.raw', pts=OUT_DIR + 'left.txt')
camRight.start_recording(encoderRight, OUT_DIR + 'right.raw', pts=OUT_DIR + 'right.txt')

# input("Waiting for keypress...")
time.sleep(5)

print("Flushing recordings")
camLeft.stop_recording()
camRight.stop_recording()

print("Done")