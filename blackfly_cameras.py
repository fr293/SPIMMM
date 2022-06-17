
# Import libraries ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PySpin is the API for the cameras
import PySpin


def set_system():
    return PySpin.System.GetInstance()


class CAMERA:

    def __init__(self, cam_list, serial_1):
        self.cam = cam_list.GetBySerial(serial_1)
        self.camInit()
        self.configure_trigger(software_trigger=True)
        self.create_window()

    # Variables
    software_trigger = True

    def camInit(self):
        self.cam.Init()
        serial_number = self.cam.DeviceSerialNumber.GetValue()
        print('\nCamera %s...' % serial_number)
        # load default configuration
        # self.cam.UserSetSelector.SetValue(PySpin.UserSetSelector_Default)
        # self.cam.UserSetLoad()

        self.cam.AcquisitionFrameRateEnable.SetValue(False)
        self.cam.ExposureMode.SetValue(PySpin.ExposureMode_Timed)
        self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        self.cam.ExposureTime.SetValue(25000)
        self.cam.GainSelector.SetValue(PySpin.GainSelector_All)
        self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)  # is contrast
        self.cam.Gain.SetValue(20)
        self.cam.BlackLevelSelector.SetValue(PySpin.BlackLevelSelector_All)  # is brightness
        self.cam.BlackLevel.SetValue(0)
        self.cam.GammaEnable.SetValue(True)
        self.cam.Gamma.SetValue(1)
        #
        # self.cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
        # self.cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)

        # set ADC bit depth and image pixel depth, size
        self.cam.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
        self.cam.AdcBitDepth.SetValue(PySpin.AdcBitDepth_Bit10)
        self.cam.OffsetX.SetValue(0)
        self.cam.OffsetY.SetValue(0)
        self.cam.Width.SetValue(2448)
        self.cam.Height.SetValue(2048)

    def configure_trigger(self, software_trigger):
        self.software_trigger = software_trigger
        # print('*** CONFIGURING TRIGGER ***\n')
        try:
            # Ensure trigger mode off
            # The trigger must be disabled in order to configure whether the source
            # is software or hardware.
            nodemap = self.cam.GetNodeMap()
            node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
            if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
                print('Unable to disable trigger mode (node retrieval). Aborting...')
                return False
            node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
            if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
                print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
                return False
            node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())
            # print('Trigger mode disabled...')
            # Select if triggers should overlap
            node_trigger_overlap = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerOverlap'))
            if not PySpin.IsAvailable(node_trigger_overlap) or not PySpin.IsWritable(node_trigger_overlap):
                print('Unable to get trigger overlap (node retrieval). Aborting...')
                return False
            node_trigger_overlap_readout = node_trigger_overlap.GetEntryByName('ReadOut')
            if not PySpin.IsAvailable(node_trigger_overlap_readout) or not PySpin.IsReadable(
                    node_trigger_overlap_readout):
                print('Unable to get trigger overlap (entry retrieval). Aborting...')
                return False
            # Retrieve integer value from entry node
            trigger_overlap_readout = node_trigger_overlap_readout.GetValue()
            # Set integer value from entry node as new value of enumeration node
            node_trigger_overlap.SetIntValue(trigger_overlap_readout)
            # print('node_exposure_mode=%s' % node_exposure_mode.GetValue())
            # print('trigger overlap set to read out...')
            # Select trigger source
            # The trigger source must be set to hardware or software while trigger mode is off.
            node_trigger_source = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerSource'))
            if not PySpin.IsAvailable(node_trigger_source) or not PySpin.IsWritable(node_trigger_source):
                print('Unable to get trigger source (node retrieval). Aborting...')
                return False

            # Software trigger activated
            if self.software_trigger:
                node_trigger_source_software = node_trigger_source.GetEntryByName('Software')
                if not PySpin.IsAvailable(node_trigger_source_software) or not PySpin.IsReadable(
                        node_trigger_source_software):
                    print('Unable to set trigger source (enum entry retrieval). Aborting...')
                    return False
                node_trigger_source.SetIntValue(node_trigger_source_software.GetValue())
            # Hardware trigger activated
            else:
                node_trigger_source_hardware = node_trigger_source.GetEntryByName('Line0')
                if not PySpin.IsAvailable(node_trigger_source_hardware) or not PySpin.IsReadable(
                        node_trigger_source_hardware):
                    print('Unable to set trigger source (enum entry retrieval). Aborting...')
                    return False
                node_trigger_source.SetIntValue(node_trigger_source_hardware.GetValue())

            # Turn trigger mode on
            # Once the appropriate trigger source has been set, turn trigger mode
            # on in order to retrieve images using the trigger.
            node_trigger_mode_on = node_trigger_mode.GetEntryByName('On')
            if not PySpin.IsAvailable(node_trigger_mode_on) or not PySpin.IsReadable(node_trigger_mode_on):
                print('Unable to enable trigger mode (enum entry retrieval). Aborting...')
                return False
            node_trigger_mode.SetIntValue(node_trigger_mode_on.GetValue())
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    def reset_trigger(self):
        try:
            nodemap = self.cam.GetNodeMap()
            node_exposure_mode = PySpin.CEnumerationPtr(nodemap.GetNode('ExposureMode'))
            node_exposure_mode_timed = node_exposure_mode.GetEntryByName('Timed')
            if not PySpin.IsAvailable(node_exposure_mode_timed) or not PySpin.IsReadable(
                    node_exposure_mode_timed):
                print('Unable to set exposure mode to timed (entry retrieval). Aborting...')
                return False
            # Retrieve integer value from entry node
            exposure_mode_timed = node_exposure_mode_timed.GetValue()
            # Set integer value from entry node as new value of enumeration node
            node_exposure_mode.SetIntValue(exposure_mode_timed)
            # print('node_exposure_mode=%s' % node_exposure_mode.GetValue())
            # print('Exposure mode set to timed...')
            node_trigger_mode = PySpin.CEnumerationPtr(nodemap.GetNode('TriggerMode'))
            if not PySpin.IsAvailable(node_trigger_mode) or not PySpin.IsReadable(node_trigger_mode):
                print('Unable to disable trigger mode (node retrieval). Aborting...')
                return False
            node_trigger_mode_off = node_trigger_mode.GetEntryByName('Off')
            if not PySpin.IsAvailable(node_trigger_mode_off) or not PySpin.IsReadable(node_trigger_mode_off):
                print('Unable to disable trigger mode (enum entry retrieval). Aborting...')
                return False
            node_trigger_mode.SetIntValue(node_trigger_mode_off.GetValue())
            # print('Trigger mode disabled...')
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    def camera_mode(self, mode):
        # -------------------------
        # Buffer handling
        # Retrieve Stream Parameters device nodemap
        s_node_map = self.cam.GetTLStreamNodeMap()

        # Retrieve Buffer Handling Mode Information
        handling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
        if not PySpin.IsAvailable(handling_mode) or not PySpin.IsWritable(handling_mode):
            print('Unable to set Buffer Handling mode (node retrieval). Aborting...\n')
            return False

        handling_mode_entry = PySpin.CEnumEntryPtr(handling_mode.GetCurrentEntry())
        if not PySpin.IsAvailable(handling_mode_entry) or not PySpin.IsReadable(handling_mode_entry):
            print('Unable to set Buffer Handling mode (Entry retrieval). Aborting...\n')
            return False

        # Set stream buffer Count Mode to manual
        stream_buffer_count_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferCountMode'))
        if not PySpin.IsAvailable(stream_buffer_count_mode) or not PySpin.IsWritable(stream_buffer_count_mode):
            print('Unable to set Buffer Count Mode (node retrieval). Aborting...\n')
            return False

        stream_buffer_count_mode_manual = PySpin.CEnumEntryPtr(stream_buffer_count_mode.GetEntryByName('Manual'))
        if not PySpin.IsAvailable(stream_buffer_count_mode_manual) or not PySpin.IsReadable(
                stream_buffer_count_mode_manual):
            print('Unable to set Buffer Count Mode entry (Entry retrieval). Aborting...\n')
            return False

        stream_buffer_count_mode.SetIntValue(stream_buffer_count_mode_manual.GetValue())
        # print('Stream Buffer Count Mode set to manual...')

        # Retrieve and modify Stream Buffer Count
        buffer_count = PySpin.CIntegerPtr(s_node_map.GetNode('StreamBufferCountManual'))
        if not PySpin.IsAvailable(buffer_count) or not PySpin.IsWritable(buffer_count):
            print('Unable to set Buffer Count (Integer node retrieval). Aborting...\n')
            return False

        buffer_count.SetValue(200)

        handling_mode_entry = handling_mode.GetEntryByName(mode)
        handling_mode.SetIntValue(handling_mode_entry.GetValue())

        # Display Buffer Info
        print('Buffer Mode: %s\n' % handling_mode_entry.GetDisplayName())
        # print('Default Buffer Handling Mode: %s' % handling_mode_entry.GetDisplayName())
        # print('Default Buffer Count: %d' % buffer_count.GetValue())
        # print('Maximum Buffer Count: %d' % buffer_count.GetMax())
        return True

    # This function sets up the camera so that it's ready for acquisition
    def create_window(self):
        try:
            nodemap = self.cam.GetNodeMap()
            node_acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode('AcquisitionMode'))

            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_acquisition_mode):
                print('Unable to set acquisition mode to continuous (enum retrieval). Aborting...')
                return False

            # Retrieve entry node from enumeration node
            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')

            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                print('Unable to set acquisition mode to continuous (entry retrieval). Aborting...')
                return False

            # Retrieve integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            # Set integer value from entry node as new value of enumeration node
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)
            # print('Acquisition mode set to continuous...')
            self.camera_mode('NewestOnly')
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    def begin_acquisition(self):
        status = self.cam.IsStreaming()
        if not status:
            self.cam.BeginAcquisition()
        # serial_number = self.cam.DeviceSerialNumber.GetValue()
        # print('Camera %s begins acquisition\n' % serial_number)

    def end_acquisition(self):
        status = self.cam.IsStreaming()
        if status:
            self.cam.EndAcquisition()
        # serial_number = self.cam.DeviceSerialNumber.GetValue()
        # print('Camera %s ends acquisition\n' % serial_number)
        return True

    # This function resets the settings of contrast and gain to their original values, and then ends acquisition
    def terminate(self):
        self.end_acquisition()
        self.set_offset_x(0)
        self.set_offset_y(0)
        self.set_width(2448)
        self.set_height(2048)
        # Deinitialize camera
        self.cam.DeInit()
        return True

    # Image acquisition ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # This function gets one image from the selected camera every time it is called upon
    def acquire_images(self):
        try:
            # Check if correct trigger type is on
            if self.software_trigger:
                if self.cam.TriggerSoftware.GetAccessMode() != PySpin.WO:
                    print('Unable to execute trigger. Aborting...')
                    return False
                # Execute Software trigger
                self.cam.TriggerSoftware.Execute()
                # Collect the image stored in the Buffer
                image_result = self.cam.GetNextImage()
                if image_result.IsIncomplete():
                    print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                    # Delete the image from the Buffer
                    image_result.Release()
                    return False
                # Make sure that image is 8bit
                # Need to erase this line when implementing 12bit images
                image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
                image_array = image_converted.GetNDArray()
                # Delete the image from the Buffer
                image_result.Release()
                return image_array, image_result.GetTimeStamp()
            else:
                print('Use the hardware to trigger image acquisition.')
                return False
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    # This function gets one image from the selected camera every time it is called upon
    def acquire_images_hardware(self):
        try:
            # 2000 is the timeout duration
            # Raise exception when cannot GetNextImage after 2000ms
            image_result = self.cam.GetNextImage(2000)
            if image_result.IsIncomplete():
                print('Image incomplete with image status %d ...' % image_result.GetImageStatus())
                image_result.Release()
                return False, False
            image_converted = image_result.Convert(PySpin.PixelFormat_Mono8, PySpin.HQ_LINEAR)
            image_array = image_converted.GetNDArray()
            image_result.Release()
            return image_array, image_result.GetTimeStamp()
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False, False

    # Acquisition parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def set_exposure(self, t):
        try:
            if self.cam.ExposureAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic exposure. Aborting...')
                return False
            self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            if self.cam.ExposureTime.GetAccessMode() != PySpin.RW:
                print('Unable to set exposure time. Aborting...')
                return False
            # Ensure desired exposure time does not exceed the maximum
            exposure_time_to_set = min(self.cam.ExposureTime.GetMax(), t)
            self.cam.ExposureTime.SetValue(exposure_time_to_set)
            exposure_time_in_ms = int(exposure_time_to_set / 1000)
            print('Exposure time set to %s ms...\n' % exposure_time_in_ms)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    def get_exposure(self):
        try:
            exposure_time = self.cam.ExposureTime.GetValue()
            return exposure_time
        except PySpin.SpinnakerException as ex:
            print('Error: %s' % ex)
            return False

    def set_gain(self, gain_value):
        try:
            if self.cam.GainAuto.GetAccessMode() != PySpin.RW:
                print('Unable to disable automatic gain. Aborting...')
                return False
            self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            if self.cam.Gain.GetAccessMode() != PySpin.RW:
                print('Unable to set gain. Aborting...')
                return False
            self.cam.Gain.SetValue(gain_value)
            print('Gain set to %s Db...\n' % gain_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def set_blacklevel(self, blacklevel_value):
        try:
            if self.cam.BlackLevelSelector.GetAccessMode() != PySpin.RW:
                print('Unable to set black level selector to all. Aborting...')
            self.cam.BlackLevelSelector.SetValue(PySpin.BlackLevelSelector_All)
            if self.cam.BlackLevel.GetAccessMode() != PySpin.RW:
                print('Unable to set black level. Aborting...')
            self.cam.BlackLevel.SetValue(blacklevel_value)
            print('Black Level set to %s \n' % blacklevel_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def set_gamma(self, gamma_value):
        try:
            if self.cam.GammaEnable.GetAccessMode() != PySpin.RW:
                print('Unable to enable gamma. Aborting...')
                return False
            self.cam.GammaEnable.SetValue(True)
            if self.cam.Gamma.GetAccessMode() != PySpin.RW:
                print('Unable to set gamma. Aborting...')
                return False
            self.cam.Gamma.SetValue(gamma_value)
            print('Gamma set to %s \n' % gamma_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    # Shape image ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def get_width(self):
        return self.cam.Width.GetValue()

    def get_width_max(self):
        return self.cam.Width.GetMax()

    def set_width(self, width_value):
        try:
            if self.cam.Width.GetAccessMode() != PySpin.RW:
                print('Unable to set image width. Aborting...')
                return False
            width_value = min(self.cam.Width.GetMax(), width_value)
            width_value = max(self.cam.Width.GetMin(), width_value)
            self.cam.Width.SetValue(width_value)
            # print('Width set to %s' % width_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def get_height(self):
        return self.cam.Height.GetValue()

    def get_height_max(self):
        return self.cam.Height.GetMax()

    def set_height(self, height_value):
        try:
            if self.cam.Height.GetAccessMode() != PySpin.RW:
                print('Unable to set image height. Aborting...')
                return False
            height_value = min(self.cam.Height.GetMax(), height_value)
            height_value = max(self.cam.Height.GetMin(), height_value)
            self.cam.Height.SetValue(height_value)
            # print('Height set to %s' % height_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def get_offset_x(self):
        return self.cam.OffsetX.GetValue()

    def get_offset_x_max(self):
        return self.cam.OffsetX.GetMax()

    def set_offset_x(self, offset_x_value):
        try:
            if self.cam.OffsetX.GetAccessMode() != PySpin.RW:
                print('Unable to set offset x. Aborting...')
                return False
            offset_x_value = min(self.cam.OffsetX.GetMax(), offset_x_value)
            offset_x_value = max(self.cam.OffsetX.GetMin(), offset_x_value)
            self.cam.OffsetX.SetValue(offset_x_value)
            # print('Offset X set to %s' % offset_x_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def get_offset_y(self):
        return self.cam.OffsetY.GetValue()

    def get_offset_y_max(self):
        return self.cam.OffsetY.GetMax()

    def set_offset_y(self, offset_y_value):
        try:
            if self.cam.OffsetY.GetAccessMode() != PySpin.RW:
                print('Unable to set offset y. Aborting...')
                return False
            offset_y_value = min(self.cam.OffsetY.GetMax(), offset_y_value)
            offset_y_value = max(self.cam.OffsetY.GetMin(), offset_y_value)
            self.cam.OffsetY.SetValue(offset_y_value)
            # print('Offset Y set to %s' % offset_y_value)
            return True
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

    def get_shape(self):
        try:
            if (self.cam.Width.GetAccessMode() != PySpin.RW) or (self.cam.Height.GetAccessMode() != PySpin.RW):
                print('Unable to set image shape. Aborting...')
                return False
            width_value = self.cam.Width.GetValue()
            height_value = self.cam.Height.GetValue()
            print('Image is {} x {} pixels\n'.format(width_value, height_value))
            return height_value, width_value
        except PySpin.SpinnakerException as ex:
            print('Error: {}'.format(ex))
            return False

