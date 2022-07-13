import tkinter as tk
from PIL import ImageTk, Image
import cv2, time
from threading import Thread

class tkintergui:
	"""Creates a gui looper"""

	def __init__(self, ):
		"""Constructor for gui"""

		self.root = tk.Tk()

		# Create a frame
		self.app = tk.Frame(self.root, bg="white")
		self.app.grid()
		# Create a label in the frame
		self.lmain = tk.Label(self.app)
		self.lmain.grid()

		self.thread = Thread(target=self.start_loop, args=())

		self.cap = cv2.VideoCapture(0)

	def video_stream(self):
		_, frame = self.cap.read()
		cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
		img = Image.fromarray(cv2image)
		imgtk = ImageTk.PhotoImage(image=img)
		self.lmain.imgtk = imgtk
		self.lmain.configure(image=imgtk)
		self.lmain.after(1, self.video_stream)

	def start_loop(self):
		self.video_stream()
		self.root.mainloop()

	def begin_thread(self):
		# Start the thread to read frames from the video stream

		self.thread.daemon = True
		self.thread.start()

new_gui = tkintergui()

new_gui.begin_thread()

while True:
	time.sleep(5)