from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
import cv2

root = Tk()
# Create a frame
frm = ttk.Frame(root)
frm.grid()
# Create a label in the frame
lmain = ttk.Label(frm, padding=10)
lmain.grid(column=0, row=0)

l1 = ttk.Label(frm, text="Hello World!")
l1.grid(sticky="N", column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)



# Capture from camera
cap = cv2.VideoCapture(0)

# function for video streaming
def video_stream():
    _, frame = cap.read()
    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
    img = Image.fromarray(cv2image)
    imgtk = ImageTk.PhotoImage(image=img)
    lmain.imgtk = imgtk
    lmain.configure(image=imgtk)
    lmain.after(1, video_stream)

video_stream()
root.mainloop()