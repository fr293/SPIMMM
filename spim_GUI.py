# ernesto zourgane emz21, noam demri nsd31, fergus riche fr293 wrote this to control the
# Selective Plane Illumination Magnetic Manipulator Microscope [SPIMMM]
# description of function: this script generates a preview of the SPIMMM cameras

# Import libraries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import matplotlib.pyplot as plt
import numpy as np
import Queue
import threading
import imageio
import time
import csv
import os
import re
import string
from tqdm import tqdm  # progress bar
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # import PIL.Image after tkinter because tkinter* import tkinter.Image and overwrite

# Import files
import spim_objects as so
import blackfly_cameras as bc

######################################################################################################################
# Initialize video recording variable
video_on = False
monitor_temp = False
stop = False
magnet_on = False
resized_image_width = 612
resized_image_height = 512
directory = '/'

# Initialize displayed image dimensions and create an empty one
large_empty_array = np.zeros((2448, 2048), dtype=np.int8)
last_image = np.copy(large_empty_array)
last_time = 0
large_empty_image = Image.fromarray(large_empty_array)
small_empty_image = large_empty_image.resize((612, 512), Image.ANTIALIAS)


# Defining functions to validate entries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def correct(inp):
    if inp.isdigit() or inp == '':
        return True
    else:
        return False


def correctf(inp):
    if inp.replace('.', '', 1).isdigit() or inp == '':
        return True
    else:
        return False


def correctfn(inp):
    if inp == '' or inp == '-':
        return True
    elif inp[0] == '-':
        return inp.replace('.', '', 1).replace('-', '', 1).isdigit()
    else:
        return inp.replace('.', '', 1).isdigit()


# Camera parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def enable_cam1_block():
    cam1_gain_field.config(state='normal')
    cam1_blacklevel_field.config(state='normal')
    cam1_gamma_field.config(state='normal')
    cam1_exposure_field.config(state='normal')


def enable_cam2_block():
    cam2_gain_field.config(state='normal')
    cam2_blacklevel_field.config(state='normal')
    cam2_gamma_field.config(state='normal')
    cam2_exposure_field.config(state='normal')


def disable_cam1_block():
    cam1_gain_field.config(state='disabled')
    cam1_blacklevel_field.config(state='disabled')
    cam1_gamma_field.config(state='disabled')
    cam1_exposure_field.config(state='disabled')


def disable_cam2_block():
    cam2_gain_field.config(state='disabled')
    cam2_blacklevel_field.config(state='disabled')
    cam2_gamma_field.config(state='disabled')
    cam2_exposure_field.config(state='disabled')


def update_gain(event, cam, gain_field):
    new_gain = float(gain_field.get())
    if new_gain > 40:
        print('Error: Value out of bound')
    else:
        cam.set_gain(new_gain)


def update_blacklevel(event, cam, blacklevel_field):
    new_blacklevel = float(blacklevel_field.get())
    if new_blacklevel > 10 or new_blacklevel < -5:
        print('Error: Value out of bound')
    else:
        cam.set_blacklevel(new_blacklevel)


def update_gamma(event, cam, gamma_field):
    new_gamma = float(gamma_field.get())
    if new_gamma > 4 or new_gamma < 0.25:
        print('Error: Value out of bound')
    else:
        cam.set_gamma(new_gamma)


def update_exposure(event, cam, exposure_field):
    new_exposure = 1000 * int(exposure_field.get())
    cam.set_exposure(new_exposure)


# Image format ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def update_roi_block():
    if camera_display.get() == 1:
        cam = cam_1
    else:
        cam = cam_2

    roi_width_value.set(cam.get_width())
    roi_width_input.set(cam.get_width())
    roi_width_slider.config(to=cam.get_width_max())
    roi_width_slider.update()
    roi_width_field.update()

    roi_height_value.set(cam.get_height())
    roi_height_input.set(cam.get_height())
    roi_height_slider.config(to=cam.get_height_max())
    roi_height_slider.update()
    roi_height_field.update()

    roi_xoffset_value.set(cam.get_offset_x())
    roi_xoffset_input.set(cam.get_offset_x())
    roi_xoffset_slider.config(to=cam.get_offset_x_max())
    roi_xoffset_slider.update()
    roi_xoffset_field.update()

    roi_yoffset_value.set(cam.get_offset_y())
    roi_yoffset_input.set(cam.get_offset_y())
    roi_yoffset_slider.config(to=cam.get_offset_y_max())
    roi_yoffset_slider.update()
    roi_yoffset_field.update()

    canvas.coords(image_on_canvas, cam.get_offset_x() / 4, cam.get_offset_y() / 4)
    global resized_image_width
    resized_image_width = cam.get_width() / 4
    global resized_image_height
    resized_image_height = cam.get_height() / 4


def image_max_size():
    if camera_display.get() == 1:
        cam = cam_1
    else:
        cam = cam_2
    global stop
    stop = True
    cam.end_acquisition()

    cam.set_offset_x(0)
    cam.set_offset_y(0)
    cam.set_width(2448)
    cam.set_height(2048)
    update_roi_block()
    update_roi_block()

    canvas.coords(image_on_canvas, 0, 0)
    global resized_image_width
    resized_image_width = 612
    global resized_image_height
    resized_image_height = 512
    cam.begin_acquisition()
    stop = False
    return True


def roi_square():
    if camera_display.get() == 1:
        cam = cam_1
    else:
        cam = cam_2
    global stop
    stop = True
    cam.end_acquisition()

    cam.set_offset_x(0)  # to reset width & height range
    cam.set_offset_y(0)
    cam.set_width(660)  # 660pixels = 200um in sample
    cam.set_height(660)
    cam.set_offset_x(600)
    cam.set_offset_y(500)
    update_roi_block()  # need 2x to update completely
    update_roi_block()

    canvas.coords(image_on_canvas, 150, 125)
    cam.begin_acquisition()
    stop = False
    return True


def disable_roi_block():
    roi_width_field.config(state='disabled')
    roi_width_slider.config(state='disabled')
    roi_height_field.config(state='disabled')
    roi_height_slider.config(state='disabled')
    roi_xoffset_field.config(state='disabled')
    roi_xoffset_slider.config(state='disabled')
    roi_yoffset_field.config(state='disabled')
    roi_yoffset_slider.config(state='disabled')
    roi_maxsize_button.config(state='disabled')
    roi_square_button.config(state='disabled')
    roi_width_field.update()
    roi_width_slider.update()
    roi_height_field.update()
    roi_height_slider.update()
    roi_xoffset_field.update()
    roi_xoffset_slider.update()
    roi_yoffset_field.update()
    roi_yoffset_slider.update()
    roi_maxsize_button.update()
    roi_square_button.update()


def enable_roi_block():
    roi_width_field.config(state='normal')
    roi_width_slider.config(state='normal')
    roi_height_field.config(state='normal')
    roi_height_slider.config(state='normal')
    roi_xoffset_field.config(state='normal')
    roi_xoffset_slider.config(state='normal')
    roi_yoffset_field.config(state='normal')
    roi_yoffset_slider.config(state='normal')
    roi_maxsize_button.config(state='normal')
    roi_square_button.config(state='normal')
    roi_width_field.update()
    roi_width_slider.update()
    roi_height_field.update()
    roi_height_slider.update()
    roi_xoffset_field.update()
    roi_xoffset_slider.update()
    roi_yoffset_field.update()
    roi_yoffset_slider.update()
    roi_maxsize_button.update()
    roi_square_button.update()


def roi_width(event, from_slider, width):
    if camera_display == 0:
        return False
    else:
        if camera_display.get() == 1:
            cam = cam_1
        else:
            cam = cam_2
        global stop
        stop = True
        cam.end_acquisition()

        if from_slider:
            roi_width_input.set(width)
        else:
            roi_width_value.set(width)
        cam.set_width(width)
        roi_xoffset_slider.config(to=cam.get_offset_x_max())
        roi_xoffset_slider.update()

        global resized_image_width
        resized_image_width = width / 4
        cam.begin_acquisition()
        stop = False
        return True


def roi_height(event, from_slider, height):
    if camera_display == 0:
        return False
    else:
        if camera_display.get() == 1:
            cam = cam_1
        else:
            cam = cam_2
        global stop
        stop = True
        cam.end_acquisition()

        if from_slider:
            roi_height_input.set(height)
        else:
            roi_height_value.set(height)
        cam.set_height(height)
        roi_yoffset_slider.config(to=cam.get_offset_y_max())
        roi_yoffset_slider.update()

        global resized_image_height
        resized_image_height = height / 4
        cam.begin_acquisition()
        stop = False
        return True


def roi_xoffset(event, from_slider, xoffset):
    if camera_display == 0:
        return False
    else:
        if camera_display.get() == 1:
            cam = cam_1
        else:
            cam = cam_2
        global stop
        stop = True
        cam.end_acquisition()

        if from_slider:
            roi_xoffset_input.set(xoffset)
        else:
            roi_xoffset_value.set(xoffset)
        yoffset = roi_yoffset_value.get()
        cam.set_offset_x(xoffset)
        roi_width_slider.config(to=cam.get_width_max())
        roi_width_slider.update()

        canvas.coords(image_on_canvas, xoffset / 4, yoffset / 4)
        cam.begin_acquisition()
        stop = False
        return True


def roi_yoffset(event, from_slider, yoffset):
    if camera_display == 0:
        return False
    else:
        if camera_display.get() == 1:
            cam = cam_1
        else:
            cam = cam_2
        global stop
        stop = True
        cam.end_acquisition()

        if from_slider:
            roi_yoffset_input.set(yoffset)
        else:
            roi_yoffset_value.set(yoffset)
        xoffset = roi_xoffset_value.get()
        cam.set_offset_y(yoffset)
        roi_height_slider.config(to=cam.get_height_max())
        roi_height_slider.update()

        canvas.coords(image_on_canvas, xoffset / 4, yoffset / 4)
        cam.begin_acquisition()
        stop = False
        return True


# Camera display control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def freeze():
    global stop
    stop = True
    print('Freeze camera display')
    freeze_indicator[0].place(x=250, y=250)


def resume():
    global stop
    stop = False
    print('Resume camera display')
    freeze_indicator[0].place(x=-1000, y=-1000)


# Camera display control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# These two function control a variable that can stop or resume the main loop
def switch_cam():
    global stop
    stop = True
    if camera_display.get() == 0:
        disable_cam1_block()
        disable_cam2_block()
        disable_roi_block()
        cam_1.end_acquisition()
        cam_2.end_acquisition()
    else:
        enable_roi_block()
        if camera_display.get() == 1:
            enable_cam1_block()
            disable_cam2_block()
            update_roi_block()
            cam_1.begin_acquisition()
            cam_2.end_acquisition()
        else:
            disable_cam1_block()
            enable_cam2_block()
            update_roi_block()
            cam_1.end_acquisition()
            cam_2.begin_acquisition()
    stop = False


def stream_image():
    time_start = time.time()
    if video_on:
        print('Start video recording...')
        # Initialize video recording
        video_image_queue = Queue.Queue()
        video_time_queue = Queue.Queue()
        # video_temp_queue = Queue.Queue()
        # start_temp()
        video(video_image_queue, video_time_queue)  # , video_temp_queue
    else:
        delay_update_image = update_image()
        delay_update_image = delay_update_image - int((time.time() - time_start) * 1000)
        if delay_update_image < 0:
            delay_update_image = 0
        # print('run time %i' % int((time.time() - time_start) * 1000))
        # print('timeout %i\n' % delay_update_image)
        window.after(delay_update_image, stream_image)


def update_image():
    global last_image
    global last_time
    delay_update_image = 100  # minimum stream framerate is 10fps
    if not stop:
        # No cam mode activated
        if camera_display.get() == 0:
            last_image = np.copy(large_empty_array)
            last_time = 0
            resized_image = small_empty_image
        else:
            if camera_display.get() == 1:
                current_exposure = int(cam_1.get_exposure())
                raw_image, last_time = cam_1.acquire_images()
            else:
                current_exposure = int(cam_2.get_exposure())
                raw_image, last_time = cam_2.acquire_images()
            last_image = np.copy(raw_image)
            new_image = Image.fromarray(raw_image)
            resized_image = new_image.resize((resized_image_width, resized_image_height), Image.ANTIALIAS)

            if current_exposure > 50000:
                delay_update_image = int(current_exposure / 500)

        image_tk = ImageTk.PhotoImage(image=resized_image)
        canvas.image_tk = image_tk
        # Changing the image on the canvas
        canvas.itemconfigure(image_on_canvas, image=image_tk)
        canvas.update()
    return delay_update_image


# Save image or video ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def set_directory():
    global directory
    new_directory = filedialog.askdirectory(initialdir=directory, title="Set saving directory")
    if not new_directory:
        print('Warning. Directory unchanged...')
        return False
    else:
        directory = new_directory
        print('Saving default directory is now %s' % directory)
        return True


def save_path(autoexp):
    if autoexp:
        sample = sample_name.get()
        dir_list = ['E', 'N', 'S', 'W']
        dir_nb = magnet_direction.get()
        direction = dir_list[dir_nb]
        amp = float(magnet_amplitude_field.get())
        regex = re.compile('[%s]' % re.escape(string.punctuation))  # replace point in amp string with A
        force = regex.sub('A', '%.1f' % amp)
        temp = str(int(float(target_temperature_input.get())))
        filename = sample + '_' + direction + '_' + force + '_' + temp
        # Create folder for new experiment inside sample folder
        filepath = os.path.join(directory, filename)
        os.makedirs(filepath)
    else:
        filename = ''
        filepath = directory
    filetypes = [('tiff files', '*.tif'), ('all files', '*.*')]
    filepath = filedialog.asksaveasfilename(initialfile=filename, initialdir=filepath, title='Select file',
                                            filetypes=filetypes)  # , defaultextension='.tif'
    # Exit if save file operation is aborted
    if not filepath:
        print('Error: empty filepath')
        return False
    else:
        filepath = os.path.splitext(filepath)[0]  # delete file extension if present
        return filepath


# This function saves the current frame once called upon
def save_image(last_img):
    filepath = save_path(False)
    if isinstance(filepath, bool):
        return False
    image_saved = Image.fromarray(last_img)
    image_saved.save(filepath + '.tif', format='TIFF')
    print('Image saved as %s.tif' % filepath)


def save_video(filepath, image_queue, time_queue, ):  # temp_queue,
    with imageio.get_writer(filepath + '.tif') as stack:
        with open(filepath + '_time_temp.csv', 'ab') as f:
            writer = csv.writer(f)
            while not image_queue.empty():
                dequeued_image = image_queue.get()
                dequeued_time = time_queue.get()
                # dequeued_temp = temp_queue.get()
                stack.append_data(dequeued_image)
                writer.writerow([dequeued_time])  # , dequeued_temp


def start_video():
    if int(cam1_exposure_field.get()) > int(frame_period_vid.get()):
        print('Warning: Frame rate too high for current exposure time')
        record_radiobutton.set('0')
        start_record_radiobutton.update()
        return False
    else:
        global video_on
        video_on = True
        video_record_indicator[0].place(x=250, y=250)
        return True


def stop_video():
    global video_on
    video_on = False
    video_record_indicator[0].place(x=-1000, y=-1000)


# For one camera registration
def video(image_queue, time_queue):  # , temp_queue
    time_start = time.time()
    # Streaming
    if video_on:
        update_image()
        # image and associated time are append to queue
        image_queue.put(np.copy(last_image))
        time_queue.put(last_time)
        # temp_queue.put(spim.tempm)
        delay_update_image = int(frame_period_vid.get())
        delay_update_image = delay_update_image - int((time.time() - time_start) * 1000)
        if delay_update_image < 0:
            delay_update_image = 0
        print('run time %i' % int((time.time() - time_start) * 1000))
        print('timeout %i\n' % delay_update_image)
        window.after(delay_update_image, lambda: video(image_queue, time_queue))  # , temp_queue
    else:
        # stop_temp()
        # Recording
        # Save path, breaks if aborted
        filepath = save_path(False)
        if isinstance(filepath, bool):
            return False
        save_video_thread = threading.Thread(name='save_video_thread', target=save_video,
                                             args=(filepath, image_queue, time_queue,))  # temp_queue,
        save_video_thread.start()

        # restart normal streaming
        stream_image()

        save_video_thread.join()
        print('Video saved as %s.tif' % filepath)


# Volume capture ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def grab_sweep_image(image_queue, time_queue, start_queue, counter):
    for cnt in range(counter):
        enqueued_image, enqueued_time = cam_1.acquire_images_hardware()
        # breaks if enqueued_image if False
        if isinstance(enqueued_image, bool):
            return False
        image_queue.put(enqueued_image)
        time_queue.put(enqueued_time)  # return time in nanos
        if cnt == 0:
            start_queue.put(enqueued_time)
            print
        # print('captured %i/%i' % (number, counter))
    return True


def save_sweep_image(image_queue, time_queue, start_queue, filepath, start_pos, distance_steps, frame_number, autoexp,
                     temperature):
    with imageio.get_writer(filepath + '.tif') as stack:  # , bigtiff=True
        with open(filepath + '.csv', 'ab') as f:
            writer = csv.writer(f)
            position = start_pos
            start_time = start_queue.get()
            for frm in range(frame_number):
                dequeued_image = image_queue.get()
                stack.append_data(dequeued_image)
                frame_time = int((time_queue.get() - start_time)/1000)  # time in micros
                if autoexp:
                    writer.writerow([frame_time, position, temperature])
                else:
                    writer.writerow([frame_time, position])
                position += distance_steps
                # print('saved %i/%i' % (frm + 1, frame_number))
    return True


def start_sweep_cfg():
    # Stop streaming
    global stop
    stop = True
    # Freeze cam1
    freeze_resume_status.set(True)
    freeze_video_radiobutton.update()
    cam_1.end_acquisition()
    cam_2.end_acquisition()
    # Configure camera
    cam_1.configure_trigger(software_trigger=False)
    cam_1.camera_mode('OldestFirst')
    cam_1.begin_acquisition()
    sweeping_indicator[0].place(x=250, y=250)
    # Stop temperature controller, because Ard can only run one process at a time
    stop_temp()


def stop_sweep_cfg():
    # Reconfigure camera
    cam_1.end_acquisition()
    print('Volume capture successfully run')
    cam_1.configure_trigger(software_trigger=True)
    cam_1.camera_mode('NewestOnly')
    sweeping_indicator[0].place(x=-1000, y=-1000)
    # Resume cam1
    freeze_resume_status.set(False)
    freeze_video_radiobutton.update()
    cam_1.begin_acquisition()
    # Restart streaming
    global stop
    stop = False
    # Start temperature control
    start_temp()


def sweep():
    frame_period = int(frame_period_vol.get())
    exposure_period = int(cam1_exposure_field.get())
    start_pos = float(lower_z_value.get())
    stop_pos = float(upper_z_value.get())
    distance_steps = float(z_step_input.get()) / 1000
    frame_number = int(np.round((stop_pos - start_pos) / distance_steps, 1)) + 1

    if stop_pos > 6.495:
        print('warning: upper position out of bounds, > 6.495')
        return False
    if frame_period < exposure_period:
        print('warning: frame period out of bounds, < exposure time')
        return False
    if video_on:
        print('warning: video recording running')
        return False

    # Region of interest undefined
    if cam_1.get_width() == 2448 and cam_1.get_height() == 2048:
        proceed = messagebox.askyesno(title='Warning',
                                      message='Region of interest not defined. Do you want to proceed?')
        if not proceed:  # Breaks if no button is clicked
            return False

    # Save path, breaks if aborted
    filepath = save_path(False)
    if isinstance(filepath, bool):
        return False
    # filepath = 'C:/Users/emz21/Desktop/bead_0A1'
    print('Sweep saved as %s.tif' % filepath)

    # Camera and Gui configuration
    start_sweep_cfg()
    print('Starting sweep')

    # Arduino configuration
    # Could need to modify the slope if we tune the temperature, add to this function
    # slope = float(mirror_slope_input.get())
    spim.take_volume_cfg(frame_number, frame_period, exposure_period, start_pos, distance_steps)
    print('Sweep will have %i steps' % frame_number)

    image_q = Queue.Queue()
    time_q = Queue.Queue()
    start_q = Queue.Queue()
    arduino_sweep_thread = threading.Thread(target=spim.take_volume)
    grab_image_thread = threading.Thread(target=grab_sweep_image, args=(image_q, time_q, start_q, frame_number,))
    save_image_thread = threading.Thread(target=save_sweep_image,
                                         args=(image_q, time_q, start_q, filepath, start_pos,
                                               distance_steps, frame_number, False, False))
    arduino_sweep_thread.start()
    grab_image_thread.start()
    save_image_thread.start()
    arduino_sweep_thread.join()
    # print('sweep thread ended')
    grab_image_thread.join()
    # print('image thread ended')
    save_image_thread.join()
    # print('save thread ended')

    stop_sweep_cfg()
    return True


# Automated experiments ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def auto_cfg():
    # Warning, region of interest undefined
    if cam_1.get_width() == 2448 and cam_1.get_height() == 2048:
        proceed = messagebox.askyesno(title='Warning',
                                      message='Region of interest not defined. Do you want to proceed?')
        if not proceed:  # Breaks if no button is clicked
            return False, False

    # Check if parameters in range
    frame_number = 41
    frame_period = 40
    exposure_period = 25
    start_pos = spim.pos  # stage current position
    stop_pos = start_pos + 0.1  # 100um depth
    distance_steps = 0.0025  # slicing with 2um steps
    volume_number = 20
    volume_period = 2000  # in millis

    if stop_pos > 6.495:
        print('warning: upper position out of bounds, > 6.495')
        return False, False
    if frame_period < exposure_period:
        print('warning: frame period out of bounds, < exposure time')
        return False, False
    if video_on:
        print('warning: video recording running')
        return False, False

    # Save path, breaks if aborted
    filepath = save_path(True)
    if isinstance(filepath, bool):
        return False, False

    # Configure GUI
    # also stops temp controller, because Ard can only run one process at a time
    temperature = spim.tempm  # copy current temp before overwrite
    start_sweep_cfg()

    # Configure arduino
    spim.take_volume_cfg(frame_number, frame_period, exposure_period, start_pos, distance_steps)
    return filepath, temperature


# Save volumes from automated experiments
def save_auto(image_queue, time_queue, start_queue, filepath, start_pos, distance_steps, frame_number, volume_number,
              temperature):
    start_time = start_queue.get()
    start_queue.put(start_time)  # re-put value in queue for next thread to read it
    for vol in range(0, 2 * volume_number, 2):
        volume_path = filepath + '_' + str(vol).zfill(2)
        with imageio.get_writer(volume_path + '.tif') as stack:  # , bigtiff=True
            with open(volume_path + '.csv', 'ab') as f:
                writer = csv.writer(f)
                position = start_pos  # first frame of each volume is at start_position
                for frm in range(frame_number):
                    # Save frame
                    dequeued_image = image_queue.get()
                    if isinstance(dequeued_image, bool):  # breaks if image is error during image acquisition
                        return False
                    stack.append_data(dequeued_image)

                    # Save experimental conditions
                    frame_time = int((time_queue.get() - start_time)/1000)  # rescale time in micros
                    writer.writerow([frame_time, position, temperature])
                    position += distance_steps  # increment position at each frame
                    # print('saved %i/%i' % (number, counter))


# Progress bar
def progress(filepath):
    filename = os.path.basename(filepath)
    for i in tqdm(range(100), desc=filename):  # 90sec experiments
        time.sleep(0.9)


# Automated experiment main function
def auto():
    offlaser()
    # Make config
    filepath, temp = auto_cfg()
    if isinstance(filepath, bool):
        return False  # breaks if incomplete
    print('Perform experiments: %s' % filepath)

    start_pos = spim.pos
    frame_number = 41
    volume_number = 21
    total_number = frame_number * volume_number
    image_q = Queue.Queue()
    time_q = Queue.Queue()
    start_q = Queue.Queue()

    # Laser on, turned off to prevent photo-bleaching
    onlaser2()
    plt.pause(1)

    grab_thread = threading.Thread(target=grab_sweep_image, args=(image_q, time_q, start_q, total_number,))
    save_thread = threading.Thread(target=save_auto,
                                   args=(image_q, time_q, start_q, filepath, start_pos, 0.0025, frame_number,
                                         volume_number, temp))
    progress_thread = threading.Thread(target=progress, args=(filepath,))  # Progress bar
    grab_thread.start()
    save_thread.start()
    progress_thread.start()

    for trigger_time in range(0, 42, 2):
        start = time.time()
        sweep_thread = threading.Thread(target=spim.take_volume)
        sweep_thread.start()
        sweep_thread.join()
        # Start magnets for 30s at first iteration
        if trigger_time == 0:
            auto_magnet()
        delay = 2 + start - time.time()
        if delay < 0:
            delay = 0
        plt.pause(delay)

    grab_thread.join()
    save_thread.join()
    # Laser off
    offlaser2()
    spim.starttempcont()

    plt.pause(47)

    onlaser2()
    spim.halttempcont()
    plt.pause(1)
    volume_path = filepath + '_90'
    start_q2 = Queue.Queue()  # This starting time will be unused
    # After relaxation volume
    sweep_thread = threading.Thread(target=spim.take_volume)
    grab_thread2 = threading.Thread(target=grab_sweep_image, args=(image_q, time_q, start_q2, 41,))
    save_thread2 = threading.Thread(target=save_sweep_image,
                                    args=(image_q, time_q, start_q, volume_path, start_pos, 0.0025, 41, True, temp,))
    sweep_thread.start()
    grab_thread2.start()
    save_thread2.start()
    sweep_thread.join()
    grab_thread2.join()
    save_thread2.join()
    progress_thread.join()
    offlaser()
    # Return normal config
    stop_sweep_cfg()
    return True


# Temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def read_temp():
    if monitor_temp:
        readout_temperature.set(spim.tempm)
        # with open(tempfile + '.csv', 'ab') as f:
        #     writer = csv.writer(f)
        #     temp_time = time.time() - start_time
        #     writer.writerow([temp_time, spim.tempm])  # , dequeued_temp
        # window.after(2000, lambda: read_temp(tempfile, start_time))
        window.after(2000, read_temp)
        return True
    else:
        return False


def start_temp():
    # block volume button
    # sweep_volume_button.config(state='disabled')
    if temperature_control.get() == 0:
        temperature_control.set(1)
        start_temperature_radiobutton.update()

    # tempfile = save_path(False)
    # start_time = time.time()

    spim.tem = float(target_temperature_input.get())
    print('Start temperature controller, target set to %.1f C ...' % spim.tem)
    # Start temperature controller
    spim.starttempcont()

    global monitor_temp
    monitor_temp = True
    # read_temp(tempfile, start_time)
    read_temp()


def stop_temp():
    # release volume button
    # sweep_volume_button.config(state='normal')
    if temperature_control.get() == 1:
        temperature_control.set(0)
        start_temperature_radiobutton.update()

    spim.halttempcont()
    readout_temperature.set(' ')

    global monitor_temp
    monitor_temp = False


def set_temp(event):
    if spim.tempcont.isAlive():
        spim.tem = float(target_temperature_input.get())
        print('Target temperature set to %.1f C ...' % spim.tem)
        return True
    else:
        print('Error')
        return False


# Magnets control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def start_magnet():
    global magnet_on
    magnet_on = True
    magnet_timed_button.config(state='disabled')
    magnet_pulse_button.config(state='disabled')
    magnet_timed_button.update()
    magnet_pulse_button.update()

    print('Magnet start')
    conf = magnet_direction.get()
    amp = float(magnet_amplitude_field.get())
    start_magnet_thread = threading.Thread(target=spim.start_magnet, args=(conf, amp,))
    start_magnet_thread.start()


def stop_magnet():
    global magnet_on
    magnet_on = False
    magnet_timed_button.config(state='normal')
    magnet_pulse_button.config(state='normal')
    magnet_timed_button.update()
    magnet_pulse_button.update()

    print('Magnet stop')
    stop_magnet_thread = threading.Thread(target=spim.stop_magnet)
    stop_magnet_thread.start()


# Close magnet if still on when closing GUI
def kill_magnet():
    if magnet_on:
        spim.stop_magnet()
        return True
    else:
        return False


def timed_magnet():
    magnet_timed_button.config(state='disabled')
    magnet_pulse_button.config(state='disabled')
    magnet_timed_button.update()
    magnet_pulse_button.update()

    print('Magnet timed')
    dur = float(magnet_duration_field.get())
    conf = magnet_direction.get()
    amp = float(magnet_amplitude_field.get())
    timed_magnet_thread = threading.Thread(target=spim.trigger_magnet, args=(dur, conf, amp,))
    timed_magnet_thread.start()

    magnet_timed_button.after(int((dur + 1) * 1000), lambda: magnet_timed_button.config(state='normal'))
    magnet_pulse_button.after(int((dur + 1) * 1000), lambda: magnet_pulse_button.config(state='normal'))


def auto_magnet():
    dur = 30
    conf = magnet_direction.get()
    amp = float(magnet_amplitude_field.get())
    timed_magnet_thread = threading.Thread(target=spim.trigger_magnet, args=(dur, conf, amp,))
    timed_magnet_thread.start()


def pulse_magnet():
    magnet_timed_button.config(state='disabled')
    magnet_pulse_button.config(state='disabled')
    magnet_timed_button.update()
    magnet_pulse_button.update()

    print('Magnet pulse')
    dur = 0.5
    conf = magnet_direction.get()
    amp = float(magnet_amplitude_field.get())
    magnet_pulse_thread = threading.Thread(target=spim.trigger_magnet, args=(dur, conf, amp,))
    magnet_pulse_thread.start()

    magnet_timed_button.after(1500, lambda: magnet_timed_button.config(state='normal'))
    magnet_pulse_button.after(1500, lambda: magnet_pulse_button.config(state='normal'))


# Stage control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def set_stage(event):
    pos = float(stage_position_input.get())
    lower_z_value.set(str(pos))
    upper_z_value.set(str(pos + 0.1))
    if mirror_tracking.get():
        spim.focus(pos)
    else:
        spim.stage(pos)


def raise_stage():
    spim.stage(0)
    stage_position_input.set(str(0))
    lower_z_value.set(str(0))
    upper_z_value.set(str(0.1))


# Laser control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def onlaser1():
    spim.open_ports()
    power = float(blue_power_input.get()) / 1000
    spim.pwr1 = power
    spim.lst1 = True
    spim.laser_power()


def onlaser2():
    spim.open_ports()
    power = float(yellow_power_input.get()) / 1000
    spim.pwr2 = power
    spim.lst2 = True
    spim.laser_power()


def offlaser1():
    spim.open_ports()
    spim.lst1 = False
    spim.laser_power()


def offlaser2():
    spim.open_ports()
    spim.lst2 = False
    spim.laser_power()


def powlaser1(event):
    spim.open_ports()
    power = float(blue_power_input.get()) / 1000
    spim.pwr1 = power
    print power
    spim.laser_power()


def powlaser2(event):
    spim.open_ports()
    power = float(yellow_power_input.get()) / 1000
    spim.pwr2 = power
    spim.laser_power()


def offlaser():
    spim.open_ports()
    spim.laser_shutdown()


if __name__ == '__main__':
    spim = so.SPIMMM()
    spim.engage()
    plt.pause(0.2)
    # spim.stage(0)
    spim.stage(6.2)
    spim.mirror(float(6.2))

    # Initialize cameras
    system = bc.set_system()
    cam_list = system.GetCameras()

    serial_1 = '18080300'  # Set camera serial numbers
    cam_1 = bc.CAMERA(cam_list, serial_1)  # Setting up the camera for acquisition

    serial_2 = '16375681'
    cam_2 = bc.CAMERA(cam_list, serial_2)

    # BEGINNING OF GUI MAINLOOP #########################################################################
    # Initiating the window for the preview's GUI
    window = Tk()
    window.title('Single Plane Illumination Magnetic Micro Manipulator')
    window.geometry('1200x600')
    # window.state('zoomed')

    # Validate commands
    reg = window.register(correct)
    regf = window.register(correctf)
    regfn = window.register(correctfn)

    cameras_parameters_frame = Frame(window, width=555, height=145, highlightbackground='gray',
                                     highlightthickness=2)
    cameras_parameters_frame.place(x=635, y=10)
    tools_parameters_frame = Frame(window, width=555, height=245, highlightbackground='gray', highlightthickness=2)
    tools_parameters_frame.place(x=635, y=160)
    export_parameters_frame = Frame(window, width=555, height=180, highlightbackground='gray', highlightthickness=2)
    export_parameters_frame.place(x=635, y=410)

    # Camera display ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Creating the canvas for the image
    canvas = Canvas(window, width=612, height=512, highlightbackground='gray', highlightthickness=2)
    canvas.place(x=10, y=10)

    # Placing the first image in the canvas
    empty_displayed = ImageTk.PhotoImage(small_empty_image, master=window)
    image_on_canvas = canvas.create_image(0, 0, anchor=NW, image=empty_displayed)

    # Camera display control ---------------------
    # camera_display gives which camera to display is used
    # 0: no cam; 1: camera1; 2: camera2
    camera_display = IntVar()
    no_cam_button = Radiobutton(window, text='No Camera', variable=camera_display, value=0, command=switch_cam,
                                indicator=0, width=10)
    no_cam_button.place(x=10, y=535)
    cam_1_button = Radiobutton(window, text='18080300', variable=camera_display, value=1, command=switch_cam,
                               indicator=0, width=10, fg='red3')
    cam_1_button.place(x=90, y=535)
    cam_2_button = Radiobutton(window, text='16375681', variable=camera_display, value=2, command=switch_cam,
                               indicator=0, width=10, fg='RoyalBlue3')
    cam_2_button.place(x=170, y=535)
    camera_display.set(0)

    # Screenshot
    save_image_button = Button(window, text='Screenshot', command=lambda: save_image(last_image), width=10)
    save_image_button.place(x=335, y=535)

    # Freeze and Resume button
    freeze_resume_status = BooleanVar()
    freeze_video_radiobutton = Radiobutton(window, text='Freeze', variable=freeze_resume_status, value=1,
                                           command=freeze, indicator=0, width=8)
    freeze_video_radiobutton.place(x=485, y=535)
    resume_video_radiobutton = Radiobutton(window, text='Resume', variable=freeze_resume_status, value=0,
                                           command=resume, indicator=0, width=8)
    resume_video_radiobutton.place(x=550, y=535)
    freeze_resume_status.set(False)

    freeze_indicator = [Label(window, text='FROZEN', fg='red')]

    # Cameras parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    camera1_block_label = Label(window, text='Blackfly 18080300', bg='brown1', width=16)
    camera1_block_label.place(x=690, y=20)
    camera2_block_label = Label(window, text='Blackfly 16375681', bg='SkyBlue1', width=16)
    camera2_block_label.place(x=945, y=20)

    # Parameters for camera 1 --------------
    cam1_gain_label = Label(window, text='Gain [0, 40]:')
    cam1_gain_label.place(x=650, y=50)
    cam1_gain_field = Entry(window, width=8, validate='key', validatecommand=(regf, '%P'), bd=2)
    cam1_gain_field.place(x=770, y=50)
    cam1_gain_field.insert(0, '20')
    cam1_gain_field.config(state='disabled')
    cam1_gain_field.bind('<Return>', lambda e: update_gain(e, cam_1, cam1_gain_field))
    cam1_gain_units_label = Label(window, text='Db')
    cam1_gain_units_label.place(x=825, y=50)

    cam1_blacklevel_label = Label(window, text='Brightness [-5, 10]:')
    cam1_blacklevel_label.place(x=650, y=70)
    cam1_blacklevel_field = Entry(window, width=8, validate='key', validatecommand=(regfn, '%P'), bd=2)
    cam1_blacklevel_field.place(x=770, y=70)
    cam1_blacklevel_field.insert(0, '0')
    cam1_blacklevel_field.config(state='disabled')
    cam1_blacklevel_field.bind('<Return>', lambda e: update_blacklevel(e, cam_1, cam1_blacklevel_field))
    cam1_blacklevel_units_label = Label(window, text='%')
    cam1_blacklevel_units_label.place(x=825, y=70)

    cam1_gamma_label = Label(window, text='Gamma [0.25, 4]:')
    cam1_gamma_label.place(x=650, y=90)
    cam1_gamma_field = Entry(window, width=8, validate='key', validatecommand=(regf, '%P'), bd=2)
    cam1_gamma_field.place(x=770, y=90)
    cam1_gamma_field.insert(0, '1')
    cam1_gamma_field.config(state='disabled')
    cam1_gamma_field.bind('<Return>', lambda e: update_gamma(e, cam_1, cam1_gamma_field))

    cam1_exposure_label = Label(window, text='Exposure [1, 10k]:')
    cam1_exposure_label.place(x=650, y=110)
    cam1_exposure_field = Entry(window, width=8, validate='key', validatecommand=(reg, '%P'), bd=2)
    cam1_exposure_field.place(x=770, y=110)
    cam1_exposure_field.insert(0, '25')
    cam1_exposure_field.config(state='disabled')
    cam1_exposure_field.bind('<Return>', lambda e: update_exposure(e, cam_1, cam1_exposure_field))
    cam1_exposure_units_label = Label(window, text='ms')
    cam1_exposure_units_label.place(x=825, y=110)

    # Parameters for camera 2 -------------
    cam2_gain_label = Label(window, text='Gain [0, 40]:')
    cam2_gain_label.place(x=900, y=50)
    cam2_gain_field = Entry(window, width=8, validate='key', validatecommand=(regf, '%P'), bd=2)
    cam2_gain_field.place(x=1020, y=50)
    cam2_gain_field.insert(0, '20')
    cam2_gain_field.config(state='disabled')
    cam2_gain_field.bind('<Return>', lambda e: update_gain(e, cam_2, cam2_gain_field))
    cam2_gain_units_label = Label(window, text='Db')
    cam2_gain_units_label.place(x=1075, y=50)

    cam2_blacklevel_label = Label(window, text='Brightness [-5, 10]:')
    cam2_blacklevel_label.place(x=900, y=70)
    cam2_blacklevel_field = Entry(window, width=8, validate='key', validatecommand=(regfn, '%P'), bd=2)
    cam2_blacklevel_field.place(x=1020, y=70)
    cam2_blacklevel_field.insert(0, '0')
    cam2_blacklevel_field.config(state='disabled')
    cam2_blacklevel_field.bind('<Return>', lambda e: update_blacklevel(e, cam_2, cam2_blacklevel_field))
    cam2_blacklevel_units_label = Label(window, text='%')
    cam2_blacklevel_units_label.place(x=1075, y=70)

    cam2_gamma_label = Label(window, text='Gamma [0.25, 4]:')
    cam2_gamma_label.place(x=900, y=90)
    cam2_gamma_field = Entry(window, width=8, validate='key', validatecommand=(regf, '%P'), bd=2)
    cam2_gamma_field.place(x=1020, y=90)
    cam2_gamma_field.insert(0, '1')
    cam2_gamma_field.config(state='disabled')
    cam2_gamma_field.bind('<Return>', lambda e: update_gamma(e, cam_2, cam2_gamma_field))

    cam2_exposure_label = Label(window, text='Exposure [1, 10k]:')
    cam2_exposure_label.place(x=900, y=110)
    cam2_exposure_field = Entry(window, width=8, validate='key', validatecommand=(reg, '%P'), bd=2)
    cam2_exposure_field.place(x=1020, y=110)
    cam2_exposure_field.insert(0, '25')
    cam2_exposure_field.config(state='disabled')
    cam2_exposure_field.bind('<Return>', lambda e: update_exposure(e, cam_2, cam2_exposure_field))
    cam2_exposure_units_label = Label(window, text='ms')
    cam2_exposure_units_label.place(x=1075, y=110)

    # Temperature control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    temperature_block_label = Label(window, text='Temperature', bg='white', width=12)
    temperature_block_label.place(x=690, y=170)

    target_temperature_input = StringVar()
    target_temperature_label = Label(window, text='Target:')
    target_temperature_label.place(x=650, y=205)
    target_temperature_field = Entry(window, textvariable=target_temperature_input, width=8, validate='key',
                                     validatecommand=(regfn, '%P'), bd=2)
    target_temperature_field.place(x=715, y=205)
    target_temperature_field.bind('<Return>', set_temp)
    target_units_label = Label(window, text='C')
    target_units_label.place(x=770, y=205)
    target_temperature_input.set('20.0')

    readout_temperature = StringVar()
    readout_temperature_label = Label(window, text='Actual:')
    readout_temperature_label.place(x=650, y=225)
    readout_temperature_field = Label(window, textvariable=readout_temperature, width=7, fg='red', bg='gray90',
                                      relief='sunken', bd=1, anchor='w')
    readout_temperature_field.place(x=715, y=225)
    readout_units_label = Label(window, text='C')
    readout_units_label.place(x=770, y=225)
    readout_temperature.set(' ')

    temperature_control = IntVar()
    start_temperature_radiobutton = Radiobutton(window, text='Start', variable=temperature_control, value=1,
                                                command=start_temp, indicator=0
                                                , width=6)
    start_temperature_radiobutton.place(x=680, y=250)
    stop_temperature_radiobutton = Radiobutton(window, text='Stop', variable=temperature_control, value=0,
                                               command=stop_temp,
                                               indicator=0, width=6)
    stop_temperature_radiobutton.place(x=730, y=250)
    temperature_control.set(0)

    # Magnets control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    magnet_block_label = Label(window, text='Magnets', bg='white', width=12)
    magnet_block_label.place(x=945, y=170)

    # Force direction
    magnet_direction = IntVar()
    north_button = Radiobutton(window, text='N', variable=magnet_direction, value=1, indicator=0, width=4)
    north_button.place(x=865, y=205)
    south_button = Radiobutton(window, text='S', variable=magnet_direction, value=2, indicator=0, width=4)
    south_button.place(x=902, y=205)
    east_button = Radiobutton(window, text='W', variable=magnet_direction, value=3, indicator=0, width=4)
    east_button.place(x=865, y=230)
    west_button = Radiobutton(window, text='E', variable=magnet_direction, value=0, indicator=0, width=4)
    west_button.place(x=902, y=230)
    magnet_direction.set(1)

    # Current amplitude
    magnet_amplitude_label = Label(window, text='Ampl. [0.1, 2.5]:')
    magnet_amplitude_label.place(x=965, y=205)
    magnet_amplitude_field = Entry(window, width=8)
    magnet_amplitude_field.place(x=1065, y=205)
    magnet_amplitude_field.insert(0, '1.0')
    magnet_amplitude_label = Label(window, text='Amps')
    magnet_amplitude_label.place(x=1120, y=205)

    magnet_duration_label = Label(window, text='Duration:')
    magnet_duration_label.place(x=965, y=225)
    magnet_duration_field = Entry(window, width=8, validate='key',
                                  validatecommand=(regf, '%P'))
    magnet_duration_field.place(x=1065, y=225)
    magnet_duration_field.insert(0, '1.0')
    magnet_duration_units_label = Label(window, text='s')
    magnet_duration_units_label.place(x=1120, y=225)

    magnet_control = IntVar()
    magnet_start_radiobutton = Radiobutton(window, text='Start', variable=magnet_control, value=1,
                                           command=start_magnet, indicator=0, width=6)
    magnet_start_radiobutton.place(x=965, y=255)
    magnet_stop_radiobutton = Radiobutton(window, text='Stop', variable=magnet_control, value=0,
                                          command=stop_magnet, indicator=0, width=6)
    magnet_stop_radiobutton.place(x=1015, y=255)
    magnet_control.set(0)

    magnet_timed_button = Button(window, text='Timed',
                                 command=timed_magnet, width=6)
    magnet_timed_button.place(x=1070, y=255)

    magnet_pulse_button = Button(window, text='Pulse',
                                 command=pulse_magnet, width=6)
    magnet_pulse_button.place(x=1125, y=255)

    # Stage control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    stage_block_label = Label(window, text='Stage', bg='white', width=12)
    stage_block_label.place(x=690, y=310)

    stage_position_input = StringVar()
    stage_position_label = Label(window, text='Position:')
    stage_position_label.place(x=650, y=340)
    stage_position_field = Spinbox(window, from_=0, to=6.45, increment=0.01, textvariable=stage_position_input,
                                   command=lambda: set_stage(True), width=8, validate='key',
                                   validatecommand=(regfn, '%P'), bd=2, wrap=True)
    stage_position_field.place(x=715, y=340)
    stage_position_field.bind('<Return>', set_stage)
    stage_units_label = Label(window, text='mm')
    stage_units_label.place(x=780, y=340)
    stage_position_input.set('6.2')

    mirror_tracking = BooleanVar()
    mirror_tracking_checkbox = Checkbutton(window, text='Keep Focus', variable=mirror_tracking)
    mirror_tracking_checkbox.place(x=650, y=365)
    mirror_tracking.set(True)

    stage_raise_button = Button(window, text='Raise',
                                command=raise_stage, width=6)
    stage_raise_button.place(x=750, y=365)

    # Laser control ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    laser_block_label = Label(window, text='Laser', bg='white', width=12)
    laser_block_label.place(x=945, y=310)

    blue_state_input = IntVar()
    blue_power_input = StringVar()
    blue_laser_label = Label(window, text='488 Laser:', bg='DeepSkyBlue2')
    blue_laser_label.place(x=865, y=340)
    blue_power_field = Entry(window, textvariable=blue_power_input, width=8, validate='key',
                             validatecommand=(reg, '%P'), bd=2)
    blue_power_field.place(x=935, y=340)
    blue_power_field.bind('<Return>', powlaser1)
    blue_units_label = Label(window, text='mW')
    blue_units_label.place(x=990, y=340)
    blue_on_radiobutton = Radiobutton(window, text='ON', variable=blue_state_input, value=1,
                                      command=onlaser1, indicator=0, width=4)
    blue_on_radiobutton.place(x=1045, y=337)
    blue_off_radiobutton = Radiobutton(window, text='OFF', variable=blue_state_input, value=0,
                                       command=offlaser1, indicator=0, width=4)
    blue_off_radiobutton.place(x=1082, y=337)
    blue_state_input.set(0)
    blue_power_input.set('10')

    yellow_state_input = IntVar()
    yellow_power_input = StringVar()
    yellow_laser_label = Label(window, text='561 Laser:', bg='gold2')
    yellow_laser_label.place(x=865, y=370)
    yellow_power_field = Entry(window, textvariable=yellow_power_input, width=8, validate='key',
                               validatecommand=(reg, '%P'), bd=2)
    yellow_power_field.place(x=935, y=370)
    yellow_power_field.bind('<Return>', powlaser2)
    yellow_units_label = Label(window, text='mW')
    yellow_units_label.place(x=990, y=370)
    yellow_on_radiobutton = Radiobutton(window, text='ON', variable=yellow_state_input, value=1,
                                        command=onlaser2, indicator=0, width=4)
    yellow_on_radiobutton.place(x=1045, y=367)
    yellow_off_radiobutton = Radiobutton(window, text='OFF', variable=yellow_state_input, value=0,
                                         command=offlaser2, indicator=0, width=4)
    yellow_off_radiobutton.place(x=1082, y=367)
    yellow_state_input.set(0)
    yellow_power_input.set('10')

    # Volume capture ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    sweep_block_label = Label(window, text='Sweep Volume', bg='white', width=12)
    sweep_block_label.place(x=690, y=420)

    lower_z_value = StringVar()
    lower_z_label = Label(window, text='Lower limit:')
    lower_z_label.place(x=650, y=450)
    lower_z_field = Entry(window, textvariable=lower_z_value, width=8, validate='key',
                          validatecommand=(regfn, '%P'))
    lower_z_field.config(state='disabled')
    lower_z_field.place(x=740, y=450)
    lower_z_units_label = Label(window, text='mm')
    lower_z_units_label.place(x=795, y=450)
    lower_z_value.set('6.2')

    upper_z_value = StringVar()
    upper_z_label = Label(window, text='Upper limit:')
    upper_z_label.place(x=650, y=470)
    upper_z_field = Entry(window, textvariable=upper_z_value, width=8, validate='key',
                          validatecommand=(regfn, '%P'))
    # upper_z_field.config(state='disabled')
    upper_z_field.place(x=740, y=470)
    upper_z_units_label = Label(window, text='mm')
    upper_z_units_label.place(x=795, y=470)
    upper_z_value.set('6.3')

    z_step_input = StringVar()
    z_step_label = Label(window, text='By Steps Of:')
    z_step_label.place(x=650, y=490)
    z_step_field = Entry(window, textvariable=z_step_input, width=8, validate='key', validatecommand=(regfn, '%P'))
    z_step_field.place(x=740, y=490)
    z_step_units_label = Label(window, text='um')
    z_step_units_label.place(x=795, y=490)
    z_step_input.set('2.5')

    frame_period_vol = IntVar()
    frame_period_vol_label = Label(window, text='Frame Period:')
    frame_period_vol_label.place(x=650, y=510)
    frame_period_vol_field = Entry(window, textvariable=frame_period_vol, width=8, validate='key',
                                   validatecommand=(regfn, '%P'))
    frame_period_vol_field.place(x=740, y=510)
    frame_period_vol_units_label = Label(window, text='ms')
    frame_period_vol_units_label.place(x=795, y=510)
    frame_period_vol.set(40)

    # mirror_slope_input = StringVar()
    # mirror_slope_label = Label(window, text='Mirror Slope', bg='yellow')
    # mirror_slope_label.place(x=730, y=575)
    # mirror_slope_field = Entry(window, textvariable=mirror_slope_input, width=10, validate='key',
    #                            validatecommand=(regfn, '%P'))
    # mirror_slope_field.place(x=660, y=575)
    # mirror_slope_field.config(state='disabled')
    # mirror_slope_input.set(-4486.982)

    sweep_volume_button = Button(window, text='Sweep volume',
                                 command=sweep, width=12)
    sweep_volume_button.place(x=670, y=540)

    sweeping_indicator = [Label(window, text='SWEEPING VOLUME', fg='red')]

    # ROI definition ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    roi_block_label = Label(window, text='Region of Interest', bg='white', width=14)
    roi_block_label.place(x=880, y=420)

    roi_width_value = IntVar()
    roi_width_input = IntVar()
    roi_width_label = Label(window, text='Width:')
    roi_width_label.place(x=840, y=450)
    roi_width_slider = Scale(window, from_=32, to=2448, orient='horizontal', sliderlength=10,
                             width=10, length=90, showvalue=False, variable=roi_width_value, resolution=4,
                             takefocus=0)
    roi_width_slider.place(x=890, y=450)
    roi_width_slider.bind('<ButtonRelease-1>', lambda e: roi_width(e, True, roi_width_value.get()))
    roi_width_slider.config(state='disabled')
    roi_width_field = Entry(window, textvariable=roi_width_input, width=6, validate='key',
                            validatecommand=(regfn, '%P'), bd=2)
    roi_width_field.place(x=990, y=450)
    roi_width_field.bind('<Return>', lambda e: roi_width(e, False, roi_width_input.get()))
    roi_width_field.config(state='disabled')
    roi_width_value.set(2448)
    roi_width_input.set(2448)

    roi_height_value = IntVar()
    roi_height_input = IntVar()
    roi_height_label = Label(window, text='Height:')
    roi_height_label.place(x=840, y=470)
    roi_height_slider = Scale(window, from_=32, to=2048, orient='horizontal', sliderlength=10,
                              width=10, length=90, showvalue=False, variable=roi_height_value, resolution=4,
                              takefocus=0)
    roi_height_slider.place(x=890, y=470)
    roi_height_slider.bind('<ButtonRelease-1>', lambda e: roi_height(e, True, roi_height_value.get()))
    roi_height_slider.config(state='disabled')
    roi_height_field = Entry(window, textvariable=roi_height_input, width=6, validate='key',
                             validatecommand=(regfn, '%P'), bd=2)
    roi_height_field.place(x=990, y=470)
    roi_height_field.bind('<Return>', lambda e: roi_height(e, False, roi_height_input.get()))
    roi_height_field.config(state='disabled')
    roi_height_value.set(2048)
    roi_height_input.set(2048)

    roi_xoffset_value = IntVar()
    roi_xoffset_input = IntVar()
    roi_xoffset_label = Label(window, text='Offset X:')
    roi_xoffset_label.place(x=840, y=490)
    roi_xoffset_slider = Scale(window, from_=0, to=0, orient='horizontal',
                               sliderlength=10, width=10, length=90, showvalue=False, variable=roi_xoffset_value,
                               resolution=4, takefocus=0)
    roi_xoffset_slider.place(x=890, y=490)
    roi_xoffset_slider.bind('<ButtonRelease-1>', lambda e: roi_xoffset(e, True, roi_xoffset_value.get()))
    roi_xoffset_slider.config(state='disabled')
    roi_xoffset_field = Entry(window, textvariable=roi_xoffset_input, width=6, validate='key',
                              validatecommand=(regfn, '%P'), bd=2)
    roi_xoffset_field.place(x=990, y=490)
    roi_xoffset_field.bind('<Return>', lambda e: roi_xoffset(e, False, roi_xoffset_input.get()))
    roi_xoffset_field.config(state='disabled')
    roi_xoffset_value.set(0)
    roi_xoffset_input.set(0)

    roi_yoffset_value = IntVar()
    roi_yoffset_input = IntVar()
    roi_yoffset_label = Label(window, text='OffsetY:')
    roi_yoffset_label.place(x=840, y=510)
    roi_yoffset_slider = Scale(window, from_=0, to=0, orient='horizontal',
                               sliderlength=10, width=10, length=90, showvalue=False, variable=roi_yoffset_value,
                               resolution=4, takefocus=0)
    roi_yoffset_slider.place(x=890, y=510)
    roi_yoffset_slider.bind('<ButtonRelease-1>', lambda e: roi_yoffset(e, True, roi_yoffset_value.get()))
    roi_yoffset_slider.config(state='disabled')
    roi_yoffset_field = Entry(window, textvariable=roi_yoffset_input, width=6, validate='key',
                              validatecommand=(regfn, '%P'), bd=2)
    roi_yoffset_field.place(x=990, y=510)
    roi_yoffset_field.bind('<Return>', lambda e: roi_yoffset(e, False, roi_yoffset_input.get()))
    roi_yoffset_field.config(state='disabled')
    roi_yoffset_value.set(0)
    roi_yoffset_input.set(0)

    roi_maxsize_button = Button(window, text='Max Image Size',
                                command=image_max_size, width=12)
    roi_maxsize_button.place(x=840, y=540)
    roi_maxsize_button.config(state='disabled')

    roi_square_button = Button(window, text='200um square',
                               command=roi_square, width=10)
    roi_square_button.place(x=940, y=540)
    roi_square_button.config(state='disabled')

    # Save a frame or a video ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    record_block_label = Label(window, text='Video', bg='white', width=12)
    record_block_label.place(x=1070, y=420)

    frame_period_vid = StringVar()
    frame_period_vid_label = Label(window, text='Frame Period:')
    frame_period_vid_label.place(x=1045, y=445)
    frame_period_vid_field = Entry(window, textvariable=frame_period_vid, width=6, validate='key',
                                   validatecommand=(regfn, '%P'))
    frame_period_vid_field.place(x=1125, y=445)
    frame_period_vid_units_label = Label(window, text='ms')
    frame_period_vid_units_label.place(x=1165, y=445)
    frame_period_vid.set('100')

    record_radiobutton = StringVar()
    start_record_radiobutton = Radiobutton(window, text='Start', variable=record_radiobutton, value=1,
                                           command=start_video, indicator=0, width=6)
    start_record_radiobutton.place(x=1070, y=465)
    stop_record_radiobutton = Radiobutton(window, text='Stop', variable=record_radiobutton, value=0,
                                          command=stop_video, indicator=0, width=6)
    stop_record_radiobutton.place(x=1120, y=465)
    record_radiobutton.set('0')

    video_record_indicator = [Label(window, text='RECORD VIDEO', fg='red')]

    # Automated experiment ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    autoexp_block_label = Label(window, text='Automated Exp.', bg='white', width=14)
    autoexp_block_label.place(x=1070, y=500)

    sample_name = StringVar()
    sample_name_label = Label(window, text='Sample Name:')
    sample_name_label.place(x=1045, y=525)
    sample_name_field = Entry(window, textvariable=sample_name, width=6, validate='key',
                              validatecommand=(regfn, '%P'))
    sample_name_field.place(x=1125, y=525)
    sample_name.set('00')

    run_autoexp_button = Button(window, text='Run',
                                command=auto, width=6)
    run_autoexp_button.place(x=1060, y=545)

    directory_button = Button(window, text='Set Dir.', command=set_directory, width=8)
    directory_button.place(x=1120, y=545)

    stream_image()

    # END OF GUI MAINLOOP ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    window.mainloop()

    # Terminating the camera
    cam_1.terminate()
    cam_2.terminate()
    cam_1 = None
    cam_2 = None
    # Clear camera list before releasing system
    cam_list.Clear()
    # Release system instance
    system.ReleaseInstance()
    del system

    # Terminate laser, stage, temp, arduino
    offlaser()
    spim.halttempcont()
    kill_magnet()
    spim.stage(0)
    plt.pause(4)  # delay for the stage to reach its home position
    spim.disengage()
    spim.close_ports()

    print('SPIM GUI successfully exited')
