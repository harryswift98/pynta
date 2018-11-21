# -*- coding: utf-8 -*-
"""
    nano_cet.py
    ===========
    Capillary Electrokinetic Tracking of Nanoparticles (nanoCET) is a technique that allows to characterize very small
    objects thanks to calculating their diffusion properties inside a capillary. The main advantage of the technique
    is that objects remain in the Field of View for extended periods of time and thus their properties can be quantified
    with a high accuracy.


    :copyright:  Aquiles Carattino <aquiles@aquicarattino.com>
    :license: AGPLv3, see LICENSE for more details
"""
import importlib
import json
import os


import time
from datetime import datetime

import h5py as h5py
import numpy as np


from multiprocessing import Queue, Process

from pynta.model.experiment.base_experiment import BaseExperiment
from pynta.model.experiment.nano_cet.decorators import (check_camera,
                                                        check_not_acquiring,
                                                        make_async_thread,
                                                        make_async_process)


from pynta.model.experiment.nano_cet.worker_saver import worker_saver
from pynta.model.experiment.nano_cet.exceptions import StreamSavingRunning
from pynta.util import get_logger


class NanoCET(BaseExperiment):
    """ Experiment class for performing a nanoCET measurement."""
    BACKGROUND_NO_CORRECTION = 0  # No backround correction
    BACKGROUND_SINGLE_SNAP = 1

    def __init__(self, filename=None):
        super().__init__()  # Initialize base class
        self.logger = get_logger(name=__name__)

        self.worker_saver_queue = Queue()

        self.load_configuration(filename)

        self.dropped_frames = 0
        self.keep_acquiring = True
        self.acquiring = False  # Status of the acquisition
        self.camera = None  # This will hold the model for the camera
        self.current_height = None
        self.current_width = None
        self.max_width = None
        self.max_height = None
        self.background = None
        self.temp_image = None  # Temporary image, used to quickly have access to 'some' data and display it to the user
        self.movie_buffer = None  # Holds few frames of the movie in order to be able to do some analysis, save later, etc.
        self.last_index = 0  # Last index used for storing to the movie buffer
        self.stream_saving_running = False
        self.async_threads = []  # List holding all the threads spawn
        self.stream_saving_process = None
        self.do_background_correction = False
        self.background_method = self.BACKGROUND_SINGLE_SNAP

        # self.connect(self.print_me, 'free_run')

    def initialize_camera(self):
        """ Initializes the camera to be used to acquire data. The information on the camera should be provided in the
        configuration file and loaded with :meth:`~self.load_configuration`. It will load the camera assuming
        it is located in pynta/model/cameras/[model].

        .. todo:: Define how to load models from outside of pynta. E.g. from a user-specified folder.
        """
        try:
            self.logger.info('Importing camera model {}'.format(self.config['camera']['model']))
            self.logger.debug('pynta.model.cameras.' + self.config['camera']['model'])

            camera_model_to_import = 'pynta.model.cameras.' + self.config['camera']['model']
            cam_module = importlib.import_module(camera_model_to_import)
        except ModuleNotFoundError:
            self.logger.error('The model {} for the camera was not found'.format(self.config['camera']['model']))
            raise
        except:
            self.logger.exception('Unhandled exception')
            raise

        cam_init_arguments = self.config['camera']['init']

        if 'extra_args' in self.config['camera']:
            self.logger.info('Initializing camera with extra arguments')
            self.logger.debug('cam_module.camera({}, {})'.format(cam_init_arguments, self.config['camera']['extra_args']))
            self.camera = cam_module.camera(cam_init_arguments, *self.config['Camera']['extra_args'])
        else:
            self.logger.info('Initializing camera without extra arguments')
            self.logger.debug('cam_module.camera({})'.format(cam_init_arguments))
            self.camera = cam_module.camera(cam_init_arguments)
            self.current_width, self.current_height = self.camera.getSize()
            self.logger.info('Camera sensor ROI: {}px X {}px'.format(self.current_width, self.current_height))
            self.max_width = self.camera.GetCCDWidth()
            self.max_height = self.camera.GetCCDHeight()
            self.logger.info('Camera sensor size: {}px X {}px'.format(self.max_width, self.max_height))

        self.camera.initializeCamera()

    @check_camera
    @check_not_acquiring
    def snap_background(self):
        """ Snaps an image that will be stored as background.
        """
        self.logger.info('Acquiring background image')
        self.camera.configure(self.config['camera'])
        self.camera.setAcquisitionMode(self.camera.MODE_SINGLE_SHOT)
        self.camera.triggerCamera()
        self.background = self.camera.readCamera()[-1]
        self.logger.debug('Got an image of {} pixels'.format(self.backgound.shape))

    @check_camera
    @check_not_acquiring
    def set_roi(self, x, y, width, height):
        """ Sets the region of interest of the camera, provided that the camera supports cropping. All the technicalities
        should be addressed on the camera model, not in this method.

        :param int x: horizontal position for the start of the cropping
        :param int y: vertical position for the start of the cropping
        :param int width: width in pixels for cropping
        :param int height: height in pixels for the cropping
        :raises ValueError: if either dimension of the cropping goes out of the camera total amount of pixels
        :returns: The final cropping dimensions, it may be that the camera limits the user desires
        """
        X = [x, x+width-1]
        Y = [y, y+height-1]
        self.logger.debug('Setting new camera ROI to x={},y={}'.format(X, Y))
        Nx, Ny = self.camera.setROI(X, Y)
        self.current_width, self.current_height =  self.camera.getSize()
        self.logger.debug('New camera width: {}px, height: {}px'.format(self.current_width, self.current_height))
        self.tempimage = np.zeros((Nx, Ny))

    @check_camera
    @check_not_acquiring
    def clear_roi(self):
        """ Clears the region of interest and returns to the full frame of the camera.
        """
        self.logger.info('Clearing ROI settings')
        self.camera.setROI(1, 1, self.max_width, self.max_height)

    @check_camera
    @check_not_acquiring
    @make_async_thread
    def snap(self):
        """ Snap a single frame. It is not an asynchronous method. To make it async, it should be placed within
        a different thread.
        """
        self.logger.info('Snapping a picture')
        self.camera.configure(self.config['camera'])
        self.camera.setAcquisitionMode(self.camera.MODE_SINGLE_SHOT)
        self.camera.triggerCamera()
        self.check_background()
        self.temp_image = self.camera.readCamera()[-1]
        self.logger.debug('Got an image of {} pixels'.format(self.temp_image.shape))

    @make_async_thread
    @check_not_acquiring
    @check_camera
    def start_free_run(self):
        """ Starts continuous acquisition from the camera, but it is not being saved.
        It starts in blocking mode, in order to free the rest of the program, this method has to be sent to a different
        thread.

        .. TODO:: Decide if this is the best strategy or it would be better to have a separate buffer method as was the  case for UUTrack.
        """
        self.logger.info('Starting a free run acquisition')
        first = True
        self.keep_acquiring = True  # Change this attribute to stop the acquisition
        self.camera.configure(self.config['camera'])
        while self.keep_acquiring:
            if first:
                self.logger.debug('First frame of a free_run')
                self.camera.setAcquisitionMode(self.camera.MODE_CONTINUOUS)
                self.camera.triggerCamera()  # Triggers the camera only once
                first = False

            data = self.camera.readCamera()
            self.logger.debug('Got {} new frames'.format(len(data)))
            for img in data:
                if self.do_background_correction and self.background_method == self.BACKGROUND_SINGLE_SNAP:
                    img -= self.background


                # This will broadcast the data just acquired with the current timestamp
                # The timestamp is very unreliable, especially if the camera has a frame grabber.
                self.queue.put({'topic':'free_run', 'data': [time.time(), img]})

            self.temp_image = data[-1]

        self.camera.stopAcq()



    @check_not_acquiring
    @check_camera
    @make_async_thread
    def start_stream(self):
        """ Starts a stream of data into a queue. It is exactly the same as :meth:`~self.start_movie` but instead of
        creating a numpy-buffer, it puts data into a queue in order to use a separate process to either process or
        save.
        If a stream is started and there is not other process taking care of clearing the queue, there are going to be
        memory issues at some point.
         """
        self.logger.info('Starting a stream acquisition')
        first = True
        self.keep_acquiring = True  # Change this attribute to stop the acquisition
        self.camera.configure(self.config['camera'])
        self.dropped_frames = 0
        i = 0

        self.check_background()

        while self.keep_acquiring:
            if first:
                self.camera.setAcquisitionMode(self.camera.MODE_CONTINUOUS)
                self.camera.triggerCamera()  # Triggers the camera only once
                first = False

            data = self.camera.readCamera() # May read more frames at once
            for img in data:

                if self.do_background_correction and self.background_method == self.BACKGROUND_SINGLE_SNAP:
                    img = img - self.background

                queue_size = float(self.queue.qsize()) * int(img.nbytes) / 1024 / 1024
                if queue_size <= self.config['saving']['max_memory']:
                    self.queue.put(img)
                else:
                    self.dropped_frames += 1
                    self.logger.info('Dropped frame')


                self.time_buffer[i % self.config['movie']['buffer_length']] = time.time()
                i += 1

            self.temp_image = data[-1]
        self.camera.stopAcq()
        self.logger.debug('Acquired {} frames'.format(i))
        self.logger.debug('Total nomber of frames dropped: {}'.format(self.dropped_frames))

    def save_image(self):
        """ Saves the last acquired image.
        """
        if self.temp_image:
            self.logger.info('Saving last acquired image')
            # Data will be appended to existing file
            file_name = self.config['saving']['filename_photo'] + '.hdf5'
            file_dir = self.config['saving']['directory']
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.logger.debug('Created directory {}'.format(file_dir))

            with h5py.File(os.path.join(file_dir, file_name), "a") as f:
                now = str(datetime.now())
                g = f.create_group(now)
                dset = g.create_dataset('image', data=self.temp_image)
                meta = g.create_dataset('metadata', data=json.dumps(self.config))
                f.flush()
            self.logger.debug('Saved image to {}'.format(os.path.join(file_dir, file_name)))
        else:
            self.logger.warning('Tried to save an image, but no image was acquired yet.')

    def save_movie(self):
        """ Saves the movie to a file.
        """
        if self.movie_buffer:
            self.logger.info('Saving the movie')
            file_name = self.config['saving']['filename_video'] + '.hdf5'
            file_dir = self.config['saving']['directory']
            if not os.path.exists(file_dir):
                os.makedirs(file_dir)
                self.logger.debug('Created directory {}'.format(file_dir))

            with h5py.File(os.path.join(file_dir, file_name), "a") as f:
                now = str(datetime.now())
                g = f.create_group(now)
                video = np.roll(self.movie_buffer, -self.last_index, axis=2)
                timestamps = np.roll(self.time_buffer, -self.last_index)
                meta = g.create_dataset('metadata', data=json.dumps(self.config))
                dset_video = g.create_dataset('video', data=video)
                dset_times = g.create_dataset('timestamps', data=timestamps)
                f.flush()

            self.logger.debug('Saved image to {}'.format(os.path.join(file_dir, file_name)))

    def add_to_stream_queue(self, data):
        timestamp = data[0]
        img = data[1]
        self.worker_saver_queue.put(img)

    def save_stream(self):
        """ Saves the queue to a file continuously. This is an async function, that can be triggered before starting
        the stream. It relies on the multiprocess library.
        """
        if self.save_stream_running:
            self.logger.warning('Tried to start a new instance of save stream')
            raise StreamSavingRunning('You tried to start a new process for stream saving')

        self.logger.info('Starting to save the stream')
        file_name = self.config['saving']['filename_video'] + '.hdf5'
        file_dir = self.config['saving']['directory']
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            self.logger.debug('Created directory {}'.format(file_dir))
        file_path = os.path.join(file_dir, file_name)
        self.stream_saving_process = Process(target=worker_saver, args=(file_path, json.dumps(self.config), self.worker_saver_queue))
        self.stream_saving_process.start()
        self.logger.debug('Started the stream saving process')

    def stop_save_stream(self):
        """ Stops saving the stream.
        """
        self.logger.info('Stopping the saving stream process')
        if not self.save_stream_running:
            self.logger.warning('The saving stream is not running. Nothing will be done.')
            return
        self.worker_saver_queue.put('Exit')


    @property
    def save_stream_running(self):
        if self.stream_saving_process is not None:
            return self.stream_saving_process.is_alive()
        else:
            return False

    def empty_queue(self):
        """ Empties the queue where the data from the movie is being stored.
        """
        self.logger.info('Clearing the logger queue')
        while not self.queue.empty() or self.queue.size() > 0:
            self.queue.get()
        self.logger.debug('Queue cleared')

    def start_waterfal(self):
        """ A waterfall is the product of summing together all the vertical values of an image and displaying them
        as lines on a 2D image. It is how spectrometers normally work. A waterfall can be produced either by binning the
        image in the vertical direction directly at the camera, or by doing it in software.
        The first has the advantage of speeding up the readout process. The latter has the advantage of working with any
        camera.
        This method will work either with 1D arrays or with 2D arrays and will generate a stack of lines.
        """
        pass

    def check_background(self):
        """ Checks whether the background is set.
        """

        if self.do_background_correction:
            self.logger.info('Setting up the background corretion')
            if self.background_method == self.BACKGROUND_SINGLE_SNAP:
                self.logger.debug('Bacground single snap')
                if self.background is None or self.background.shape != [self.current_width, self.current_height]:
                    self.logger.warning('Background not set. Defaulting to no background...')
                    self.background = None
                    self.do_background_correction = False

    def __exit__(self, *args):
        super(NanoCET, self).__exit__(*args)
        if not self.worker_saver_queue.empty():
            self.logger.info('Emptying the saver queue')
            self.logger.debug('There are {} elements in the queue'.format(self.worker_saver_queue.qsize()))
            while not self.worker_saver_queue.empty():
                self.worker_saver_queue.get()
