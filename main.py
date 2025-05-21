import nibabel as nib
import numpy as np
from tkinter import Frame,LEFT, Tk, Label, Button, StringVar, Entry, Scale, HORIZONTAL, Radiobutton, Text, Toplevel
from PIL import Image, ImageTk
from skimage.transform import rescale, resize, downscale_local_mean
import os
import json
import platform
import matplotlib.cm as cm
import psutil

current_os = platform.system()
index_json = r"QC_logs.json"
resize_size = 400

win_cardiac_path = None
partitions = psutil.disk_partitions(all=True)
for p in partitions:
    if 'HCMNIH' in os.listdir(p.device):
        win_cardiac_path = p.device

if win_cardiac_path is None:
    exit('Cardiac path not found')

# S for Lara labtop
# Z for yuanhan desktop
# win_cardiac_path = 'Z:\\' 


with open(index_json, 'r') as file:
    data = json.load(file)

def save_qc():
    qc_text =radio_var.get() + ':' + editable_text_box.get("1.0", "end-1c")
    js_key = windows_to_linux_path(file_paths[current_file_index])
    if '_ED.nii.gz' in file_paths[current_file_index]:
        data[js_key]['ED_Comments'] = qc_text
    elif '_ES.nii.gz' in file_paths[current_file_index]:
        data[js_key]['ES_Comments'] = qc_text
    json.dump(data, open(index_json, 'w'), indent=4)

def load_qc():
    js_key = windows_to_linux_path(file_paths[current_file_index])
    if '_ED.nii.gz' in file_paths[current_file_index]:
        if 'ED_Comments' in data[js_key]:
            qc_text = data[js_key]['ED_Comments']
            option = qc_text.split(':')[0]
            comment = qc_text.split(':')[1]
            radio_var.set(option)
            editable_text_box.insert("1.0", comment)
    elif '_ES.nii.gz' in file_paths[current_file_index]:
        if 'ES_Comments' in data[js_key]:
            qc_text = data[js_key]['ES_Comments']
            option = qc_text.split(':')[0]
            comment = qc_text.split(':')[1]
            radio_var.set(option)
            editable_text_box.insert("1.0", comment)

def jump_to_file():
    if scan_text_box.get("1.0", "end-1c") == '':
        return None
    file_index = int(scan_text_box.get("1.0", "end-1c")) - 1
    global current_file_index, current_data, slice_index, animation_running,current_label
    stop_animation()  # Stop the current animation
    if current_file_index < len(file_paths) - 1:
        current_file_index = file_index
    else:
        current_file_index = 0  # Loop back to the first file

    # Load the next file
    current_data = load_nii_gz(file_paths[current_file_index])
    current_label = load_nii_gz(label_paths[current_file_index])

    current_file_var.set(file_paths[current_file_index])
    slice_index = 0  # Reset to the first slice
    editable_text_box.delete("1.0", "end") 

    load_qc()

    update_index_display()  # Update the file and slice index
    stop_animation()
    start_animation()  # Start the animation

def load_nii_gz(file_path):
    """Load the .nii.gz file and return the data as a NumPy array."""
    try:
        nii = nib.load(file_path)
        data = nii.get_fdata()
        if len(data.shape) == 4:
        # return resize(data[:,:,:,0], (resize_size, resize_size,data.shape[2]), anti_aliasing=False,preserve_range=True)
            return data[:,:,:,0]
        else:
        # return resize(data, (resize_size, resize_size,data.shape[2]), anti_aliasing=False,preserve_range=True)
            return data
    except FileNotFoundError:
        popup = Toplevel(root)
        popup.title("Popup Window")
        popup.geometry("350x130")
        Label(popup, text="File Not Found, \n That means the segmentation module had not produce results for this patient").pack(pady=20)
        Button(popup, text="Close", command=popup.destroy).pack(pady=10)


    

def normalize_image(slice_):
    """Normalize the image slice to the range 0-255."""
    slice_min = np.min(slice_)
    slice_max = np.max(slice_)
    normalized = 255 * (slice_ - slice_min) / (slice_max - slice_min) + 0.0000000000000001
    # return normalized.astype(np.uint8)
    colormap = cm.get_cmap('grey')
    colored_image = colormap(normalized / 255.0)  # Apply colormap
    colored_image = (colored_image[:, :, :3] * 255).astype(np.uint8)  # Convert to 8-bit RGB
    return colored_image

def normalize_label(label_):
    
    label_min = 0
    label_max = 3
    # label_ = resize(label_, (resize_size, resize_size), anti_aliasing=True, preserve_range=True)
    normalized = 255 * (label_ - label_min) / (label_max - label_min) + 0.0000000000000001
    normalized = normalized.astype(np.uint8)
    colormap = cm.get_cmap('magma')
    colored_label = colormap(normalized / 255.0)  # Apply colormap
    # colored_label = resize(colored_label, (resize_size, resize_size, 3), anti_aliasing=True, preserve_range=True)
    colored_label = (colored_label[:, :, :3] * 255).astype(np.uint8)  # Convert to 8-bit RGB
    return colored_label

def update_index_display():
    """Update the text box with the current file and slice index."""
    index_var.set(f"File: {current_file_index + 1}/{len(file_paths)}, Slice: {slice_index + 1}/{current_data.shape[2]}")

def change_animation_speed(new_speed):
    """Change the animation speed."""
    global animation_speed
    animation_speed = int(new_speed)

def animate_slices():
    """Animate slices of the current file."""
    
    global slice_index, animation_running
    if not animation_running:
        return  # Stop animation if the flag is False

    slice_ = current_data[:, :, slice_index]
    label_ = current_label[:, :, slice_index]

    slice_ = resize(slice_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)
    label_ = resize(label_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)
    

    normalized = normalize_image(slice_)
    normalized_label = normalize_label(label_)

    # print(normalized.shape, normalized_label.shape)

    image = Image.fromarray(normalized)
    label = Image.fromarray(normalized_label)
    photo = ImageTk.PhotoImage(image=image)
    photo_l = ImageTk.PhotoImage(image=label)
    image_label.config(image=photo)
    image_label.image = photo

    label_label.config(image=photo_l)
    label_label.image = photo_l

    # Combine the content of image_label and label_label
    combined_image = Image.fromarray((0.6*normalized + 0.4*normalized_label).astype(np.uint8))
    combined_photo = ImageTk.PhotoImage(image=combined_image)
    combined_label.config(image=combined_photo)
    combined_label.image = combined_photo

    update_index_display()  # Update the index display
    slice_index = (slice_index + 1) % current_data.shape[2]  # Loop through slices
    root.after(animation_speed, animate_slices)  # Adjust the delay for animation speed

def stop_animation():
    """Stop the animation."""
    global animation_running,slice_index
    # slice_index = 0 
    animation_running = False

def start_animation():
    """Start the animation."""
    global animation_running
    animation_running = True
    # slice_index = 0  # Reset to the first slice
    animate_slices()

def load_next_file():
    """Load the next .nii.gz file and restart the animation."""
    global current_file_index, current_data, slice_index, animation_running,current_label
    stop_animation()  # Stop the current animation
    if current_file_index < len(file_paths) - 1:
        current_file_index += 1
    else:
        current_file_index = 0  # Loop back to the first file

    # Load the next file
    current_data = load_nii_gz(file_paths[current_file_index])
    current_label = load_nii_gz(label_paths[current_file_index])

    current_file_var.set(file_paths[current_file_index])
    slice_index = 0  # Reset to the first slice
    editable_text_box.delete("1.0", "end") 

    load_qc()

    update_index_display()  # Update the file and slice index
    stop_animation()
    start_animation()  # Start the animation

def load_previous_file():
    """Load the previous .nii.gz file and restart the animation."""
    global current_file_index, current_data, slice_index, animation_running,current_label
    stop_animation()  # Stop the current animation
    if current_file_index > 0:
        current_file_index -= 1
    else:
        current_file_index = len(file_paths) - 1  # Loop back to the last file

    # Load the previous file
    current_data = load_nii_gz(file_paths[current_file_index])
    current_label = load_nii_gz(label_paths[current_file_index])

    current_file_var.set(file_paths[current_file_index])
    slice_index = 0  # Reset to the first slice
    editable_text_box.delete("1.0", "end") 

    load_qc()

    update_index_display()  # Update the file and slice index
    stop_animation()
    start_animation()  # Start the animation

def linux_to_windows_path(linux_path, cardiac_path = win_cardiac_path): 
    """
    Convert a Linux file path to a Windows file path.
    
    Parameters:
        linux_path (str): The Linux file path to convert.
        
    Returns:
        str: The converted Windows file path.
    """
    if not linux_path:
        return None

    # Replace "/" with "\\"
    windows_path = linux_path.replace("/", "\\")

    # print(windows_path)

    # Optionally handle root paths (e.g., "/mnt/c" to "C:\\")
    if windows_path.startswith("\\mnt\\storage\\home\\ym1413\\cardiac\\"):
        drive_letter = cardiac_path
        windows_path = windows_path.replace("\\mnt\\storage\\home\\ym1413\\cardiac\\", drive_letter)
    else:

        windows_path = windows_path.replace('\\cardiac\\',cardiac_path)

    return windows_path

def windows_to_linux_path(windows_path, cardiac_path = win_cardiac_path):
    """
    Convert a Windows file path to a Linux file path.
    
    Parameters:
        windows_path (str): The Windows file path to convert.
        
    Returns:
        str: The converted Linux file path.
    """

    if not windows_path:
       
        return None

    # Replace "\\" with "/"
    windows_path = windows_path.replace(win_cardiac_path, "\\cardiac\\")
    windows_path = windows_path.replace("\\", "/")

    # Optionally handle root paths (e.g., "C:\\" to "/mnt/c")


    

    return os.path.dirname(windows_path)

def _previous_slice():
    """Display the previous slice of the current file."""
    global slice_index
    slice_index = (slice_index - 1) % current_data.shape[2]  # Loop through slices
    slice_ = current_data[:, :, slice_index]
    label_ = current_label[:, :, slice_index]

    slice_ = resize(slice_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)
    label_ = resize(label_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)

    normalized = normalize_image(slice_)
    normalized_label = normalize_label(label_)

    # print(normalized.shape, normalized_label.shape)

    image = Image.fromarray(normalized)
    label = Image.fromarray(normalized_label)
    photo = ImageTk.PhotoImage(image=image)
    photo_l = ImageTk.PhotoImage(image=label)
    image_label.config(image=photo)
    image_label.image = photo

    label_label.config(image=photo_l)
    label_label.image = photo_l

    # Combine the content of image_label and label_label
    combined_image = Image.fromarray((0.6*normalized + 0.4*normalized_label).astype(np.uint8))
    combined_photo = ImageTk.PhotoImage(image=combined_image)
    combined_label.config(image=combined_photo)
    combined_label.image = combined_photo
    update_index_display()  # Update the index display

def _next_slice():
    """Display the next slice of the current file."""
    global slice_index
    slice_index = (slice_index + 1) % current_data.shape[2]  # Loop through slices
    slice_ = current_data[:, :, slice_index]
    label_ = current_label[:, :, slice_index]

    slice_ = resize(slice_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)
    label_ = resize(label_, (resize_size, resize_size), anti_aliasing=False,preserve_range=True)

    normalized = normalize_image(slice_)
    normalized_label = normalize_label(label_)

    # print(normalized.shape, normalized_label.shape)

    image = Image.fromarray(normalized)
    label = Image.fromarray(normalized_label)
    photo = ImageTk.PhotoImage(image=image)
    photo_l = ImageTk.PhotoImage(image=label)
    image_label.config(image=photo)
    image_label.image = photo

    label_label.config(image=photo_l)
    label_label.image = photo_l

    # Combine the content of image_label and label_label
    combined_image = Image.fromarray((0.6*normalized + 0.4*normalized_label).astype(np.uint8))
    combined_photo = ImageTk.PhotoImage(image=combined_image)
    combined_label.config(image=combined_photo)
    combined_label.image = combined_photo
    update_index_display()  # Update the index display

def zoom(event, label):
    """Zoom in or out on the image displayed in the label."""
    global current_data, current_label, slice_index
    scale_factor = 2.0 if event.delta > 0 else 1.0
    slice_ = current_data[:, :, slice_index]
    label_ = current_label[:, :, slice_index]
    normalized = normalize_image(slice_)
    normalized_label = normalize_label(label_)
    image = Image.fromarray(normalized)
    label_image = Image.fromarray(normalized_label)
    new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    label_image = label_image.resize(new_size, Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image=image)
    photo_l = ImageTk.PhotoImage(image=label_image)
    if label == image_label:
        label.config(image=photo)
        label.image = photo
    elif label == label_label:
        label.config(image=photo_l)
        label.image = photo_l
    elif label == combined_label:
        combined_image = Image.fromarray((0.6 * np.array(image) + 0.4 * np.array(label_image)).astype(np.uint8))
        combined_photo = ImageTk.PhotoImage(image=combined_image)
        label.config(image=combined_photo)
        label.image = combined_photo



file_paths = []
label_paths = []
for i in data.keys():
    ED_img_path = linux_to_windows_path(os.path.join(i,'lvsa_SR_ED.nii.gz'))
    ES_img_path = linux_to_windows_path(os.path.join(i,'lvsa_SR_ES.nii.gz'))

    file_paths.append(ED_img_path)
    file_paths.append(ES_img_path)

    ED_lab_path = linux_to_windows_path(os.path.join(i,'seg_lvsa_SR_ED.nii.gz'))
    ES_lab_path = linux_to_windows_path(os.path.join(i,'seg_lvsa_SR_ES.nii.gz'))

    label_paths.append(ED_lab_path)
    label_paths.append(ES_lab_path)

assert len(file_paths) == len(label_paths)

current_file_index = 0
current_data = load_nii_gz(file_paths[current_file_index])
current_label = load_nii_gz(label_paths[current_file_index])
slice_index = 0
animation_running = False
animation_speed = 150  # Default speed in milliseconds


root = Tk()
root.title("HCM NIfTI QC Viewer(V1.0)" + current_os)
root.geometry("1600x900")

label_frame = Frame(root)
label_frame.pack()


# Display the first slice of the first file
image_label = Label(label_frame)
image_label.pack(side= LEFT,expand=True, fill='both')
# image_label.bind("<MouseWheel>", lambda event: zoom(event, image_label))
combined_label = Label(label_frame)
combined_label.pack(side=LEFT,expand=True, fill='both')
# combined_label.bind("<MouseWheel>", lambda event: zoom(event, combined_label))
label_label = Label(label_frame)
label_label.pack(side= LEFT,expand=True, fill='both')
# label_label.bind("<MouseWheel>", lambda event: zoom(event, label_label))
# Add a text box to show the current file and slice index
index_var = StringVar()
index_entry = Entry(root, textvariable=index_var, state="readonly", justify="center", font=("Arial", 12),width=135)
index_entry.pack()
update_index_display()  # Display initial file and slice index

# Add a text box to show the current file path
current_file_var = StringVar()
current_file_entry = Entry(root, textvariable=current_file_var, state="readonly", justify="center", font=("Arial", 12), width=135)
current_file_entry.pack()
current_file_var.set(file_paths[current_file_index])  # Display initial file path

# Add Start, Stop, Next File, and Previous File buttons



start_button = Button(root, text="Start Animation", command=start_animation)
start_button.pack()

stop_button = Button(root, text="Stop Animation", command=stop_animation)
stop_button.pack()

next_pre_frame = Frame(root)
next_pre_frame.pack()
next_button = Button(next_pre_frame, text="Back", command=load_previous_file)
next_button.pack(side=LEFT)
scan_text_box = Text(next_pre_frame, height=1, width=4)
scan_text_box.pack(side=LEFT)
go_button = Button(next_pre_frame, text="Go", command=jump_to_file)
go_button.pack(side=LEFT)
previous_button = Button(next_pre_frame, text="Next", command=load_next_file)
previous_button.pack(side=LEFT)

# Add a scale to change the animation speed

slice_control = Frame(root)
slice_control.pack()


next_slice_button = Button(slice_control, text="-", command=_previous_slice)
next_slice_button.pack(side=LEFT)

speed_scale = Scale(slice_control, from_=50, to=300, orient=HORIZONTAL, label="Animation Speed (ms)", command=change_animation_speed)
speed_scale.set(animation_speed)  # Set the default speed
speed_scale.pack(side=LEFT) 

previous_slice_button = Button(slice_control, text="+", command=_next_slice)
previous_slice_button.pack(side=LEFT)


# Start the Tkinter main loop
# Add three radio buttons (single choice)
option_frame = Frame(root)
option_frame.pack()

radio_var = StringVar(value="unclassified")  # Default value

radio_button1 = Radiobutton(option_frame, text="Accept", variable=radio_var, value="accept")
radio_button1.pack(side=LEFT)

radio_button2 = Radiobutton(option_frame, text="Reject", variable=radio_var, value="reject")
radio_button2.pack(side=LEFT)

radio_button3 = Radiobutton(option_frame, text="Fine-Tune", variable=radio_var, value="finetune")
radio_button3.pack(side=LEFT)

radio_button4 = Radiobutton(option_frame, text="Unclassified", variable=radio_var, value="unclassified")
radio_button4.pack(side=LEFT)

editable_text_box = Text(root, height=2, width=50)
editable_text_box.pack()

start_button = Button(root, text="Save QC", command=save_qc)
start_button.pack()

load_qc()
root.mainloop()
