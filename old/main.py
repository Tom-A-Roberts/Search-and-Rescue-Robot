import math

import PIL.Image

print("Importing...")
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import requests
from tqdm import tqdm
import torch
import cv2
from PIL import Image
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
mpl.use('Qt5Agg')
import numpy as np

print("Finished imports")

print("Setting up models..")
# model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14")
# processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
print("Models loaded")

# url = "http://images.cocodataset.org/val2017/000000039769.jpg"
# image: PIL.Image.Image = Image.open(requests.get(url, stream=True).raw)

ymax = 8
ymin = 0

def stretch_value(x):
    stretch_magnitude = 2
    stretch_center = 20
    stretch_width = 1

    x = math.atan((x-stretch_center)/stretch_width)*stretch_magnitude + 1.6*stretch_magnitude

    return x


def live_plotter(x_vec, y1_data, line1, identifier = '', pause_time = 0.001):
    global ymin, ymax
    if line1 == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        fig = plt.figure(figsize=(13, 6))
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line1, = ax.plot(x_vec, y1_data, '-', alpha=0.8)
        # update plot label/title
        plt.ylabel('confidence')
        plt.title('Title: {}'.format(identifier))
        plt.show()

    line1.set_ydata(y1_data)
    plt.ylim([ymin, ymax])
    # if np.min(y1_data) <= ymin:
    #     ymin = np.min(y1_data)
    #
    # if np.max(y1_data) >= ymax:
    #     ymax = np.max(y1_data)
    # plt.ylim([ymin, ymax])
    #
    # ymin += 0.5
    # ymax -= 0.5

    # return line so we can update it again in the next iteration
    return line1


size = 100
x_vec = np.linspace(0,1,size+1)[0:-1]
y_vec = np.random.randn(len(x_vec))
y_vec = np.array([0]*size)
line1 = []


cv2.namedWindow("preview")
vc = cv2.VideoCapture(0)

if vc.isOpened(): # try to get the first frame
    rval, frame = vc.read()
else:
    rval = False

while rval:

    rval, frame = vc.read()

    cv2.imshow("preview", frame)

    #print(type(frame))

    color_coverted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(color_coverted)
    av = np.average(
        frame,
        axis=None
    )

    inputs = processor(text=["a photo of a ball"], images=pil_image, padding=True)
    inputs["input_ids"] = torch.tensor(inputs["input_ids"])
    inputs["attention_mask"] = torch.tensor(inputs["attention_mask"])
    inputs["pixel_values"] = torch.tensor(np.array(inputs["pixel_values"]))
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
    probs = logits_per_image.softmax(dim=1)  # we can take the softmax to get the label probabilities

    if logits_per_image[0] > 5:
        y_vec[-1] = stretch_value(logits_per_image[0])
        line1 = live_plotter(x_vec,y_vec,line1)
        y_vec = np.append(y_vec[1:],0.0)

    key = cv2.waitKey(20)
    if key == 27: # exit on ESC
        break

vc.release()
cv2.destroyWindow("preview")