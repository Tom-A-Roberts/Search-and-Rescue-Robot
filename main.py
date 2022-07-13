import PIL
import gui.GUI_Manager as gui
import time
from multiprocessing import Queue
import CLIP_Manager
import cv2

def clamp(num, min_value, max_value):
	return max(min(num, max_value), min_value)

def brighten_image(image: PIL.Image):
	brightness_centre = 0.5
	brighten_power = 3

	stat = PIL.ImageStat.Stat(image)
	r, g, b, _ = stat.mean
	brightness = (r+g+b)/3
	brightness /= 255

	image = PIL.ImageEnhance.Brightness(image).enhance(1 + ((brightness_centre - brightness) * brighten_power))
	return image

has_started_processing = False

def process_frame(_CLIP_AI, frame, text):
	global has_started_processing
	cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
	_img = PIL.Image.fromarray(cv2image)
	_img = brighten_image(_img)

	if not has_started_processing:
		has_started_processing = True
		print("Started processing")

	_vis, similarity_score = _CLIP_AI.find_CLIP_similarity([text], _img)
	similarity_score = (similarity_score - 20) / 10
	similarity_score = clamp(similarity_score, 0, 1)
	return _vis, similarity_score


if __name__ == '__main__':
	CLIP_AI = CLIP_Manager.CLIPProcessor()

	print("Starting up camera process...")
	frame_queue = Queue()
	vis1_queue = Queue()
	GUIObject = gui.GUIProcess(frame_queue, vis1_queue)
	GUIObject.start()

	search_text = "A photo of a plant"

	while True:

		if not frame_queue.empty():
			frame_value = frame_queue.get()
			GUIObject.send_frame_down_pipe.value = 0
			vis, score = process_frame(CLIP_AI, frame_value, search_text)
			vis1_queue.put((vis, score, search_text))
		else:
			GUIObject.send_frame_down_pipe.value = 1

		time.sleep(0.1)
		if GUIObject.stopping.value == 1:
			break
