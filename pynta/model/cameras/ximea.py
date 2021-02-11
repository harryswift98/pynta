# -*- coding: utf-8 -*-
"""
The driver file to use a camera that uses xiapi
"""
import numpy as np
from ximea import xiapi
from pynta.model.cameras.base_camera import BaseCamera
from pynta.model.cameras.exceptions import CameraNotFound, WrongCameraState, CameraException
cam=xiapi.camera()
#here add in all of the imports


#impliment all of these functions
class Camera(BaseCamera):
    def __init__(self, camera):
        super().__init__(camera)
        self.cam_num = camera
        self.max_width = 0
        self.max_height = 0
        self.width = None
        self.height = None
        self.mode = None
        self.X = None
        self.Y = None
        self.friendly_name = None
        
        
    @not_implemented
    def initialize(self):
        """
        Initializes the camera.
        """
        #function checks if camera is attached and opens it if it finds one
        #need to figure out what happens if >2 devices
        if cam.get_pNumberDevices==0:
            raise CameraNotFound('No Camera Found')
        elif cam.get_pNumberDevices==1:
            self.camera=xiapi.camera()
            self.camera.xiOpenDevice()
            
        
        self.max_width = 
        self.max_height = 0
        width = self.camera.get_width()
        height = self.camera.get_height()
        offsetX=self.camera.get_offsetX()
        offsetY=self.camera.get_offsetY()
        self.X = (offsetX,offsetX+width)
        self.Y = (offsetY,offsetY+height)
        self.friendly_name = None
        self.max_width = self.GetCCDWidth()
        self.max_height = self.GetCCDHeight()
        self.camera.trigger_software
        return True

    @not_implemented
    def trigger_camera(self):
        """
        Triggers the camera.
        """
        if self.camera.get_acquisition_status=='XI_ON':
            logger.warning('Triggering an already grabbing camera')
        else:
            if self.mode == self.MODE_CONTINUOUS:
                #grab images
                
            elif self.mode == self.MODE_SINGLE_SHOT:
                #grab an image
        pass

    @not_implemented
    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.
        :param int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        :return:
        """
        if mode == self.MODE_CONTINUOUS:
            #find and add way to change acq mode
            self.camera.set_trigger_selector(XI_TRIG_SEL_ACQUISITION_START)
        elif mode == self.MODE_SINGLE_SHOT:
            #do the same for single shot
            self.camera.set_trigger_selector(XI_TRIG_SEL_FRAME_START)
            
        self.mode = mode

    @not_implemented
    def acquisition_ready(self):
        """
        Checks if the acquisition in the camera is over.
        """
        
        pass

    #@not_implemented
    def set_exposure(self, exposure):
        """
        Sets the exposure of the camera.
        """
        self.cam.set_exposure(exposure)
        self.exposure = exposure

    #@not_implemented
    def get_exposure(self):
        """
        Gets the exposure time of the camera.
        """
        self.exposure=self.cam.get_exposure()
        return self.exposure

    @not_implemented
    def read_camera(self):
        """
        Reads the camera
        """
        if self.camera.get_acqisition_status == XI_OFF:
            raise WrongCameraState('You need to trigger the camera before reading from it')
        
        if self.mode == self.MODE_SINGLE_SHOT:
            self.camera.xiGetimage(img)
            self.camera.xiStopAcquisition
            
        else:
            frames= []
            nframes= self.camrea.xiGetImage(acq_nframe)
            logger.debug(f'{self.camrea.xiGetImage(acq_nframe)} frames available')
            if nframes:
                frames=[None]*nframes
                for i in range(nframes):
                    frames[i] = 
                    
                
                        
            
            
            

    @not_implemented
    def set_ROI(self, X, Y):
        """ Sets up the ROI. Not all cameras are 0-indexed, so this is an important
        place to define the proper ROI.

        :param list X: array type with the coordinates for the ROI X[0], X[1]
        :param list Y: array type with the coordinates for the ROI Y[0], Y[1]
        :return: X, Y lists with the current ROI information
        """
        return X, Y


    @not_implemented
    def get_size(self):
        """Returns the size in pixels of the image being acquired. This is useful for checking the ROI settings.
        """
        pass

    #@not_implemented
    def getSerialNumber(self):
        """Returns the serial number of the camera.
        """
        self.SerialNumber= self.camera.get_device_sn
        return self.SerialNumber

    @not_implemented
    def GetCCDWidth(self):
        """
        Returns the CCD width in pixels
        """
        return self.X

    @not_implemented
    def GetCCDHeight(self):
        """
        Returns: the CCD height in pixels
        """
        return self.Y

    @not_implemented
    def stopAcq(self):
        """Stops the acquisition without closing the connection to the camera."""
        self.camera.xiStopAcquisition
        

    @not_implemented
    def set_binning(self, xbin, ybin):
        """
        Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.
        
        :param xbin:
        :param ybin:
        self.camera.set_binning_horizontal(xbin)
        self.camera.set_binning_vertical(ybin)
        :return:
        
        """
        pass

    @not_implemented
    def clear_binning(self):
        """
        Clears the binning of the camera to its default value.
        """
        self.camera.set_binning_horizontal(1)
        self.camera.set_binning_vertical(1)
        pass

    @not_implemented
    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        self.camera.xiCloseDevice

