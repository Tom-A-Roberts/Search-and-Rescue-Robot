import tkinter as tk
from PIL import ImageTk, Image
import cv2, time
from threading import Thread

class tkintergui:
	"""Creates a gui looper"""

	def __init__(self, ):
		"""Constructor for gui"""

		self.thread = Thread(target=self.start_loop, args=())


def start_loop():
	print("Here", flush=True)
	cap = cv2.VideoCapture(0)

	root = tk.Tk()

	# Create a frame
	app = tk.Frame(root, bg="white")
	app.grid()
	# Create a label in the frame
	lmain = tk.Label(app)
	lmain.grid()

	def video_stream():
		_, frame = cap.read()
		if not frame is None:
			print(type(frame), flush=True)
			print(frame.empty(), flush=True)
			cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
			img = Image.fromarray(cv2image)
			imgtk = ImageTk.PhotoImage(image=img)
			lmain.imgtk = imgtk
			lmain.configure(image=imgtk)
		lmain.after(1, video_stream)

	video_stream()
	root.mainloop()


thread = Thread(target=start_loop, args=())
thread.daemon = True
thread.start()

#
while True:
	time.sleep(5)