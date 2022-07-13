import math
import time
from multiprocessing import Process, Value
from tkinter import *
from tkinter import ttk

import PIL
import cv2
import numpy as np
from PIL import ImageTk, Image, ImageEnhance, ImageStat


class FPSCounter:
	"""
	Class that tracks the number of occurrences ("counts") of an
	arbitrary event and returns the frequency in occurrences
	(counts) per second. The caller must increment the count.
	"""

	def __init__(self):
		self.frame_times = []
		self.start_t = time.time()

	def calculate_fps(self):
		end_t = time.time()
		time_taken = end_t - self.start_t
		self.start_t = end_t
		self.frame_times.append(time_taken)
		self.frame_times = self.frame_times[-20:]
		fps = len(self.frame_times) / sum(self.frame_times)
		return fps

def brighten_image(image: PIL.Image):
	brightness_centre = 0.5
	brighten_power = 3

	stat = ImageStat.Stat(image)
	r, g, b, _ = stat.mean
	brightness = (r+g+b)/3
	brightness /= 255

	image = ImageEnhance.Brightness(image).enhance(1 + ((brightness_centre - brightness) * brighten_power))
	return image

class GUIProcess(Process):
	def __init__(self, frame_queue, vis1_queue):
		# execute the base constructor
		Process.__init__(self)
		# initialize integer attribute
		self.stopping = Value('i', 0)
		self.send_frame_down_pipe = Value('i', 0)
		self.frame_queue = frame_queue
		self.vis1_queue = vis1_queue


	def stop(self):
		self.stopping.value = 1

	def run(self, ):
		"""Grab and show video frames without multithreading."""
		cap = cv2.VideoCapture(0)
		fps = FPSCounter()
		root = Tk()
		root.title('Video Viewer')
		root.protocol("WM_DELETE_WINDOW", self.stop)
		app = ttk.Frame(root)
		app.grid()

		title_label_1 = ttk.Label(app, text="Searching for: ", font=("Times New Roman", 15))
		title_label_1.grid(sticky="N", column=0, row=0, pady=5)

		webcam_viewer = ttk.Label(app)
		webcam_viewer.grid(column=0, row=1)
		webcam_viewer_label = ttk.Label(app, text="Video Feed", font=("Times New Roman", 15))
		webcam_viewer_label.config(background='black', foreground="white")
		webcam_viewer_label.grid(sticky="N", column=0, row=1, pady=5)

		vis1_viewer = ttk.Label(app)
		vis1_viewer.grid(column=1, row=1)
		vis1_viewer_label = ttk.Label(app, text="AI Attention", font=("Times New Roman", 15))
		vis1_viewer_label.config(background='black', foreground="white")
		vis1_viewer_label.grid(sticky="N", column=1, row=1, pady=5)

		print("Camera process started.")

		while True:
			grabbed, frame = cap.read()
			frame: np.ndarray = frame
			if not grabbed or self.stopping.value == 1:
				root.destroy()
				break

			# Sending data:
			if self.send_frame_down_pipe.value == 1:
				if self.frame_queue.empty():
					self.frame_queue.put(frame)

			# Recieved data:
			if not self.vis1_queue.empty():
				(vis1_image, score, search_text) = self.vis1_queue.get()
				vis1_image = PIL.Image.fromarray(vis1_image)
				width, height = vis1_image.size
				vis1_image = vis1_image.resize((width*2, height*2), Image.ANTIALIAS)
				vis1_imgtk = PIL.ImageTk.PhotoImage(image=vis1_image)
				vis1_viewer.imgtk = vis1_imgtk
				vis1_viewer.configure(image=vis1_imgtk)
				vis1_viewer_label.configure(text=f"AI Attention\nConfidence: {score*100:.1f}%")
				title_label_1.configure(text="Searching for: " + str(search_text))


			# Processing:
			iterations_per_sec = fps.calculate_fps()
			cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec),
						(10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))

			cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
			img = PIL.Image.fromarray(cv2image)
			img = brighten_image(img)
			imgtk = PIL.ImageTk.PhotoImage(image=img)
			webcam_viewer.imgtk = imgtk
			webcam_viewer.configure(image=imgtk)

			root.update()
