# Kit Beyer
# GENEActivFile class meant ot store the contents of a GENEActiv .bin data
# file. Methods will be developed for reading and writing the file (and
# converting to other types??) etc. Borrowed IP from previous R package
# (Kit Beyer) and Python modules (David Ding)
#
#
# NOTES:
# - temperature is only sampled once per page but is currently inserted at
#   each measurement so it can be held in the same data table, this is
#   consistent with the GENEARead R package behaviour
#
# TODO
# - check page numbers
# - create pdf
# - check args etc in functions
# - dcoumentation

import time
import datatable as dt

class GENEActivFile:

    def __init__(self, file_path):

        '''initialize GENEActivFile'''

        self.file_path = file_path      # path to .bin file
        self.header = {}                # header dictionary
        self.pages_read = None          # actual pages read from file
        self.data_packet = None         # hexadecimal data from entire file
        self.dataview_start = None      # start page of current dataview
        self.dataview_end = None        # end page of current dataview
        self.dataview = None            # current dataview (subset of data)


    def read(self):

        '''read text header and hex data from GENEActiv .bin file'''

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
                        line[colon + 1:].rstrip('\x00').rstrip())
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


    def view_data(self, start = 1, end = 900, temperature = True,
                  calibrate = True):

        '''parse and view a subset of the data in the file'''

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
        if calibrate:
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
                if calibrate:
                    accel_x = (accel_x * 100 - x_offset) / x_gain
                    accel_y = (accel_y * 100 - y_offset) / y_gain
                    accel_z = (accel_z * 100 - z_offset) / z_gain

                # append values to dataview dict
                dataview['accel_x'].append(accel_x)
                dataview['accel_y'].append(accel_y)
                dataview['accel_z'].append(accel_z)
                dataview['light'].append(light)
                dataview['button'].append(button)
                            

        # add tempreature if requested
        if temperature:

            # create temp key in dict
            dataview['temp'] = []

            # get all temp lines from data packet (1 per page)
            temp_chunk = [self.data_packet[i]
                          for i in range(int((start - 1) * 10 + 5),
                                         int(end * 10), 10)]

            # parse temp from temp lines and insert into dict
            for temp_line in temp_chunk:
                colon = temp_line.index(':')
                dataview['temp'].extend([float(temp_line[colon + 1:])] * 300)

        # populate self.dataview dataframe
        self.dataview = dt.Frame(dataview)
                            
        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s')

        return self.dataview
        
    def create_pdf(self, folder_path, hours = 4):

        '''create a pdf summary of this GENEActiv .bin file'''

        pass

#------------------------------------------------------------------------------


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

ga_file = GENEActivFile(bin_file_path)

ga_file.read()
ga_file.view_data(1,900)












