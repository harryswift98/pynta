# -*- coding: utf-8 -*-
"""
The driver file to use a camera that uses XiAPI
"""
import numpy as np

#here add in all of the imports


#impliment all of these functions
    @not_implemented
    def initialize(self):
        """
        Initializes the camera.
        """
        self.max_width = self.GetCCDWidth()
        self.max_height = self.GetCCDHeight()
        return True

    @not_implemented
    def trigger_camera(self):
        """
        Triggers the camera.
        """
        pass

    @not_implemented
    def set_acquisition_mode(self, mode):
        """
        Set the readout mode of the camera: Single or continuous.
        :param int mode: One of self.MODE_CONTINUOUS, self.MODE_SINGLE_SHOT
        :return:
        """
        self.mode = mode

    def get_acquisition_mode(self):
        """
        Returns the acquisition mode, either continuous or single shot.
        """
        return self.mode

    @not_implemented
    def acquisition_ready(self):
        """
        Checks if the acquisition in the camera is over.
        """
        pass

    @not_implemented
    def set_exposure(self, exposure):
        """
        Sets the exposure of the camera.
        """
        self.exposure = exposure

    @not_implemented
    def get_exposure(self):
        """
        Gets the exposure time of the camera.
        """
        return self.exposure

    @not_implemented
    def read_camera(self):
        """
        Reads the camera
        """
        pass

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

    @not_implemented
    def getSerialNumber(self):
        """Returns the serial number of the camera.
        """
        pass

    @not_implemented
    def GetCCDWidth(self):
        """
        Returns the CCD width in pixels
        """
        pass

    @not_implemented
    def GetCCDHeight(self):
        """
        Returns: the CCD height in pixels
        """
        pass

    @not_implemented
    def stopAcq(self):
        """Stops the acquisition without closing the connection to the camera."""
        pass

    @not_implemented
    def set_binning(self, xbin, ybin):
        """
        Sets the binning of the camera if supported. Has to check if binning in X/Y can be different or not, etc.

        :param xbin:
        :param ybin:
        :return:
        """
        pass

    @not_implemented
    def clear_binning(self):
        """
        Clears the binning of the camera to its default value.
        """
        pass

    @not_implemented
    def stop_camera(self):
        """Stops the acquisition and closes the connection with the camera.
        """
        pass

