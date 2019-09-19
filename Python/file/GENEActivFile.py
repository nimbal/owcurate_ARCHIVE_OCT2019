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

import time
import datatable as dt

class GENEActivFile:

    def __init__(self, file_path):

        '''initialize GENEActivFile'''

        self.file_path = file_path      # path to .bin file
        self.header = {}                # header dictionary
        self.pagecount = None           # actual pages read from file
        self.pagecount_match = None     # does pagecount read match header
        self.data_packet = None         # hexadecimal data from entire file
        self.dataview_start = None      # start page of current dataview
        self.dataview_end = None        # end page of current dataview
        self.dataview = None            # current dataview (subset of data)


    def read(self):

        '''read text header and hex data from GENEActiv .bin file'''

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


        def check_pagecount():

            '''Check to see if number of pages read matches header'''

            # set match to true
            self.pagecount_match = True

            # get page counts
            pagecount = len(self.data_packet) / 10
            header_pagecount = int(self.header['Number of Pages'])

            # check if pages read is an integer (lines read is multiple of 10)
            if not pagecount.is_integer():

                # set match to false and display warning
                self.pagecount_match = False
                print(f"****** WARNING: Pages read ({pagecount}) is not",
                      f"an integer, data may be corrupt.\n")

            # check if pages read matches header count
            if pagecount != header_pagecount:

                # set match to false and display warning
                self.pagecount_match = False
                print(f"****** WARNING: Pages read ({pagecount}) not equal to",
                      f"'Number of Pages' in header ({header_pagecount}).\n")

            # store pagecount as attribute
            self.pagecount = pagecount

        # start timer
        start_time = time.time()
        print(f'Reading {self.file_path}...', end = ' ')
  
        # read header and page packet
        header_packet = read_bin()

        # parse header
        parse_header(header_packet)

        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s\n')

        # confirm number of pages read matches header
        check_pagecount()


    def view_data(self, start = 1, end = 900, temperature = True,
                  calibrate = True):

        '''parse and view a subset of the data in the file'''

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

        # check start and end values compared to number of pages
        # also check that data has been read and header values exist

        if not self.header or self.data_packet is None or self.pagecount is None:
            print('****** WARNING: Cannot view data because file has not',
                  'been read.')
            return

        # start timer
        start_time = time.time()
        print('Parsing data to view...', end = ' ')

        # store passed arguments before checking and modifying
        oldstart = start
        oldend = end

        # check start and end for acceptable values
        if start < 1: start = 1
        elif start > self.pagecount: start = round(self.pagecount)

        if end < start: end = start
        elif end > self.pagecount: end = round(self.pagecount)
        
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
                    for i in range(start * 10 - 1, end * 10, 10)]
        
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
                          for i in range((start - 1) * 10 + 5, end * 10, 10)]

            # parse temp from temp lines and insert into dict
            for temp_line in temp_chunk:
                colon = temp_line.index(':')
                dataview['temp'].extend([float(temp_line[colon + 1:])] * 300)

        # populate self.dataview dataframe
        self.dataview = dt.Frame(dataview)
                            
        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s\n')

        # display message if start and end values were changed
        if oldstart != start or oldend != end:
            print('****** WARNING: Start or end values were modified to fit',
                  'acceptable range.\n',
                  f'       Old range: {oldstart} to {oldend}\n',
                  f'       New range: {start} to {end}.\n')

        return self.dataview
        
    def create_pdf(self, folder_path, hours = 4):

        '''create a pdf summary of this GENEActiv .bin file'''

        # start timer
        start_time = time.time()
        print('Creating pdf summary...', end = ' ')

        #







        # display time
        diff_time = round(time.time() - start_time, 3)
        print(f'{diff_time} s\n')

        #return file path




