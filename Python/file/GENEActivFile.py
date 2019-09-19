# Kit Beyer
# GENEActivFile class meant ot store the contents of a GENEActiv .bin data
# file. Methods will be developed for reading and writing the file (and
# converting to other types??) etc. Borrowed IP from previous R package
# (Kit Beyer) and Python modules (David Ding)
#
#
# TODO
# - get data
# - calibrate
# - add temperature
# - check page numbers

import time
#import numpy as np # double check if thisis this needed??
#import pandas as pd
import datatable as dt

class GENEActivFile:

    def __init__(self, file_path):

        '''initialize GENEActivFile'''

        self.file_path = file_path
        self.header = {}
        self.pages_read = None
        self.data_packet = None
        self.dataview_start = None
        self.dataview_end = None
        self.dataview = None


    def read(self):

        '''read this GENEActiv .bin file and parse into header and data'''

        # start timer
        start_time = time.time()
        print(f'Reading {self.file_path}...', end = ' ')


        def read_bin():

            '''read lines from a GENEActiv .bin file'''

            # open file
            bin_file = open(self.file_path, 'r', encoding = 'utf-8')

            # read file
            line_packet = [line[:-1] for line in bin_file.readlines()]

            # close file
            bin_file.close()

            # parse into header and data packets
            header_packet = line_packet[:59]
            self.data_packet = line_packet[59:]

            # page count
            self.pages_read = len(self.data_packet) / 10

            return header_packet


        def parse_header(header_packet):

            '''parse the header packet read from a GENEActiv .bin file'''

            self.header = {}

            for line in header_packet:

                # create key value pair from each line of the header that
                # contains a pair
                try:
                    colon = line.index(":")
                    self.header[line[:colon]] = (
                        line[colon+1:].rstrip('\x00').rstrip())
                except ValueError:
                    pass
                

        # read header and page packet
        header_packet = read_bin()

        # parse header
        parse_header(header_packet)

        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s')

        # confirm number of pages - self.pages_read
        # count actual pages - and provide warnings if doesn't match header
        # and/or pages or if incomplete pages (multiple of 10)


    def view_data(self, start = 1, end = 900, calibrate = True):

        '''view a subset of the data in the file'''

        # check start and end values compared to number of pages
        # also check that data has been read and header values exist

        # start timer
        start_time = time.time()
        print('Parsing data to view...', end = ' ')

        def uint2int(unsigned_value, sign_bit):

                '''convert an unsigned integer (in two's complement
                representation) to a signed integer''' 

                # x + x_twos_comp = 2^N
                # x = 2^N - x_twos_comp
                # x_twos_comp = 2^N - x

                # unsigned_value must be between 0 and 2^sign_bit - 1
                # inclusive otherwise give error

                signed_value = (unsigned_value - 2**sign_bit
                                if unsigned_value > 2**(sign_bit - 1) - 1
                                else  unsigned_value)

                return signed_value


        # initialize/reset variables
        self.dataview_start = start
        self.dataview_end = end
        dataview = {"accel_x" : [],
                    "accel_y" : [],
                    "accel_z" : [],
                    "light"   : [],
                    "button"  : []}


        # get calibration variables from header
        if calibrate is True:
            x_gain = int(self.header['x gain'])
            y_gain = int(self.header['y gain'])
            z_gain = int(self.header['z gain'])
            x_offset = int(self.header['x offset'])
            y_offset = int(self.header['y offset'])
            z_offset = int(self.header['z offset'])
            
        # grab chunk of data from packet
        data_chunk = [self.data_packet[i]
                    for i in range(int(start * 10 - 1), int(end * 10), 10)]
        
        # loop through pages
        for data_line in data_chunk:

            # loop through 300 measurements in each page
            for meas_index in range(300):

                # parse measurement from line and convert from hex to bin
                meas = data_line[meas_index * 12 : (meas_index + 1) * 12]
                meas = bin(int(meas, 16))[2:]
                meas = meas.zfill(48)

                # parse each signal from measurement and convert to int
                accel_x = int(meas[0:12], 2)
                accel_y = int(meas[12:24], 2)
                accel_z =  int(meas[24:36], 2)
                light = int(meas[36:46], 2)
                button = int(meas[46], 2)
                # res = int(meas[47], 2)   # NOT USED FOR NOW

                # convert accelerometer data to signed integer
                accel_x = uint2int(accel_x, 12)
                accel_y = uint2int(accel_y, 12)
                accel_z = uint2int(accel_z, 12)

                # calibrate accelerometers
                if calibrate is True:
                    accel_x = (accel_x * 100 - x_offset) / x_gain
                    accel_y = (accel_y * 100 - y_offset) / y_gain
                    accel_z = (accel_z * 100 - z_offset) / z_gain

                # append values to dataview dict
                dataview['accel_x'].append(accel_x)
                dataview['accel_y'].append(accel_y)
                dataview['accel_z'].append(accel_z)
                dataview['light'].append(light)
                dataview['button'].append(button)  

        # populate self.dataview dataframe
        self.dataview = dt.Frame(dataview)
                            
        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s')

        return self.dataview
        
    def create_pdf(folder_path):

        '''create a pdf summary of this GENEActiv .bin file'''

        pass

#------------------------------------------------------------------------------


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

ga_file = GENEActivFile(bin_file_path)

ga_file.read()
ga_file.view_data(1,900)












