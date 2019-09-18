# Kit Beyer
# GENEActivFile class meant ot store the contents of a GENEActiv .bin data
# file. Methods will be developed for reading and writing the file (and
# converting to other types??) etc. Borrowed IP from previous R package
# (Kit Beyer) and Python modules (David Ding)
#
#
# TODO
# - calibrate
# - add temperature
# - check page numbers

import time
import datatable as dt

class GENEActivFile:

    def __init__(self, file_path):

        '''initialize GENEActivFile'''

        self.file_path = file_path
        self.header = {}
        self.pages_read = None
        self.data = dt.Frame({"accel_x" : [],
                              "accel_y" : [],
                              "accel_z" : [],
                              "light"   : [],
                              "button"  : []})


    def read(self, pages = -1):
        # pages: any neg number = all, else number of pages

        '''read this GENEActiv .bin file and parse into header and data'''

        
        def read_bin(file_path, pages):

            '''read lines from a GENEActiv .bin file'''

            # start timer
            start = time.time()
            print(f'Reading {file_path}...', end = ' ')

            # open file
            bin_file = open(file_path, 'r', encoding = 'utf-8')

            # read pages
            # adds empty strings if more pages than in file
            if pages >= 0:
                line_packet = [bin_file.readline()[:-1]
                               for line in range(59 + pages*10)]
            else:
                line_packet = [line[:-1] for line in bin_file.readlines()]

            # close file
            bin_file.close()

            # parse into header and data packets
            header_packet = line_packet[:59]
            data_packet = line_packet[59:]
                
            # display time
            diff = round(time.time() - start, 3)
            print(f'{diff} s')

            return header_packet, data_packet


        def parse_header(header_packet):

            '''parse the header packet read from a GENEActiv .bin file'''

            self.header = {}

            # start timer
            start = time.time()
            print('Parsing header...', end = ' ')

            for line in header_packet:

                # create key value pair from each line of the header that
                # contains a pair
                try:
                    colon = line.index(":")
                    self.header[line[:colon]] = (
                        line[colon+1:].rstrip('\x00').rstrip())
                except ValueError:
                    pass

            # display time
            diff = round(time.time() - start, 3)
            print(f'{diff} s')


        def parse_data(data_packet):

            '''parse the data packet read from a GENEActiv .bin file'''

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
  
            # initialize variables
            lines_removed = None
            pages_removed = None
            self.data = dt.Frame({"accel_x" : [],
                                  "accel_y" : [],
                                  "accel_z" : [],
                                  "light"   : [],
                                  "button"  : []})

            # start timer
            start = time.time()
            print('Parsing data...', end = ' ')

            # remove blank lines at end (if more pages requested than exist)
            try:

                # find and remove blanks at end of read (if parges arg > pages)
                blank_index = data_packet.index('')
                num_lines = len(data_packet)
                data_packet = data_packet[:blank_index]

                # count lines and pages removed
                lines_removed = num_lines - blank_index
                pages_removed = lines_removed / 10

            except ValueError: # if no blanks found
                pass


            # page count
            self.pages_read = len(data_packet) / 10

            # loop through pages
            for page in range(round(self.pages_read)):

                # parse data line from page lines (line 10 of 10)
                data_line = data_packet[page * 10 + 9]

                # loop through 300 measurements in each page
                for meas_index in range(300):

                    # parse measurement from line and convert from hex to bin
                    meas = data_line[meas_index * 12 : (meas_index + 1) * 12]
                    meas = bin(int(meas, 16))[2:]
                    meas = meas.zfill(48)

                    # parse each signal from measurement and add to data
                    self.data.rbind(
                        dt.Frame({"accel_x" : [uint2int(int(meas[0:12], 2), 12)],
                                  "accel_y" : [uint2int(int(meas[12:24], 2), 12)],
                                  "accel_z" : [uint2int(int(meas[24:36], 2), 12)],
                                  "light"   : [int(meas[36:46], 2)],
                                  "button"  : [int(meas[46], 2)]}))
                                # "res" : int(meas[47], 2)   # NOT USED FOR NOW
                        
            # display time
            diff = round(time.time() - start, 3)
            print(f'{diff} s')

            # display warning if blank pages (lines) removed from packet
            if lines_removed is not None:
                print(f'****** WARNING: Blank pages encountered.',
                      f'{pages_removed} pages ({lines_removed} lines)',
                      f'were removed ******')

            return data_packet


        # read header and page packet
        header_packet, data_packet = read_bin(self.file_path, pages)

        # parse header
        parse_header(header_packet)

        # parse data
        self.data_packet = parse_data(data_packet)

        # confirm number of pages - self.pages_read
        # count actual pages - and provide warnings if doesn't match header
        # and/or pages or if incomplete pages (multiple of 10)


    def create_pdf(folder_path):

        '''create a pdf summary of this GENEActiv .bin file'''

        pass

#------------------------------------------------------------------------------


bin_file_path = (
    '/Users/kbeyer/repos/test_data/OND06_SBH_9248_01_SE01_GABL_GA_LA.bin')

ga_file = GENEActivFile(bin_file_path)

ga_file.read(-1)


ga_file.data.head()










