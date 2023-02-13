import time
import signal
import subprocess
import prctl

import libcamera
import picamera2.formats as formats
from picamera2 import Picamera2
from picamera2.encoders import Encoder, H264Encoder
from picamera2.outputs import Output

def hz_to_us(hz):
	return int(1000000 / hz)
	
FULL_SIZE = (4056, 3040) # About 10 FPS
HALF_SIZE = (2028, 1520) # About 40 FPS
FPS50_SIZE = (2016, 1080) # 50 FPS as reported by the sensor

CAM_RIGHT = 1
CAM_LEFT = 0

EXPOSURE = hz_to_us(500)
DURLIMIT = (hz_to_us(10), hz_to_us(10)) # 10 FPS
BITRATE = 19485000 # 19.845 Mbps, or 196 GiB for two cameras in 12h

class FfmpegOutput(Output):
	def __init__(self, output_filename, pts=None):
		super().__init__(pts=pts)
		self.ffmpeg = None
		self.output_filename = output_filename

	def start(self):
		general_options = ['-loglevel', 'warning',
						   '-y']  # -y means overwrite output without asking
		# We have to get FFmpeg to timestamp the video frames as it gets them. This isn't
		# ideal because we're likely to pick up some jitter, but works passably, and I
		# don't have a better alternative right now.
		video_input = ['-use_wallclock_as_timestamps', '1',
					   '-thread_queue_size', '32',  # necessary to prevent warnings
					   '-s', '2016x1080',
					   '-f', 'rawvideo',
					   '-pixel_format', 'rgb24',
					   '-i', '-']
		video_codec = ['-c:v', 'libx264',
					   '-b:v', str(BITRATE),
					   '-preset', 'ultrafast']

		command = ['ffmpeg'] + general_options + video_input + video_codec + self.output_filename.split()
		# The preexec_fn is a slightly nasty way of ensuring FFmpeg gets stopped if we quit
		# without calling stop() (which is otherwise not guaranteed).
		print(command)
		self.ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE, preexec_fn=lambda: prctl.set_pdeathsig(signal.SIGKILL))
		super().start()

	def stop(self):
		super().stop()
		if self.ffmpeg is not None:
			self.ffmpeg.stdin.close()  # FFmpeg needs this to shut down tidily
			self.ffmpeg.terminate()
			self.ffmpeg = None

	def outputframe(self, frame, keyframe=True, timestamp=None):
		if self.recording:
			self.ffmpeg.stdin.write(frame)
			self.ffmpeg.stdin.flush()  # forces every frame to get timestamped individually
			self.outputtimestamp(timestamp)

def create_video_configuration(self, main={}, raw=None, transform=libcamera.Transform(),
								colour_space=libcamera.ColorSpace.Sycc(), buffer_count=10, controls={}, display="main",
								encode="main", queue=False) -> dict:
	"""Make a configuration suitable for video recording."""
	if self.camera is None:
		raise RuntimeError("Camera not opened")
	main = self._make_initial_stream_config({"format": "RGB888", "size": FPS50_SIZE}, main)
	self.align_stream(main, optimal=True)
	raw = self._make_initial_stream_config({"format": self.sensor_format, "size": self.sensor_resolution}, raw)
	if raw is not None:
		self.align_stream(raw, optimal=True)
	config = {"use_case": "video",
				"transform": transform,
				"colour_space": colour_space,
				"buffer_count": buffer_count,
				"queue": queue,
				"main": main,
				"lores": None,
				"raw": raw,
				"controls": controls}
	self._add_display_and_encode(config, display, encode)
	return config

camLeft = Picamera2(CAM_LEFT)
camRight = Picamera2(CAM_RIGHT)

print("Configuring cameras")

cfgLeft = create_video_configuration(camLeft, main={'size': FPS50_SIZE}, controls={"FrameDurationLimits": DURLIMIT, "ExposureTime": EXPOSURE, "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off})
camLeft.encode_stream_name = "main"

# cfgRight = create_video_configuration(camLeft, main={'size': FPS50_SIZE}, controls={"FrameDurationLimits": DURLIMIT, "ExposureTime": EXPOSURE, "NoiseReductionMode": libcamera.controls.draft.NoiseReductionModeEnum.Off})
# camRight.encode_stream_name = "main"

camLeft.configure(cfgLeft)
# camRight.configure(cfgRight)

encoderLeft = Encoder()#H264Encoder(BITRATE)
# encoderRight = Encoder()#H264Encoder(BITRATE)

outputLeft = FfmpegOutput("/home/cnewman/bd1_share/local_data/left.mkv", pts='/home/cnewman/bd1_share/local_data/left.txt')
# outputRight = FfmpegOutput("/home/cnewman/bd1_share/local_data/right.mkv", pts='/home/cnewman/bd1_share/local_data/right.txt')

print("Settling cameras")
time.sleep(2)

print("Starting recording")
camLeft.start_recording(encoderLeft, outputLeft)
# camRight.start_recording(encoderRight, outputRight)
# input("Waiting for keypress...")
time.sleep(5)
print("Flushing recordings")
camLeft.stop_recording()
# camRight.stop_recording()
print("Done")