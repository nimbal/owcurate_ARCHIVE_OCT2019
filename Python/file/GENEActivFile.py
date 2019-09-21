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
#
# TO DO
# - add downsample option to view_data
# - use os for path and file concatenation, etc.
# - TEST DATA OUTPUT TO ENSURE READ AND CONVERSION ARE ACCURATE
# - TEST LIGHT VALUES SPECIFICALLY (COMPARE TO GENEARead?)
# - is dt.Frame necessary or is dictionary better??
# 
#

import os
import shutil
import datatable as dt
import fpdf
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle

mplstyle.use('fast')

class GENEActivFile:

    def __init__(self, file_path):

        '''initialize GENEActivFile'''

        self.file_path = file_path      # path to .bin file
        self.header = {}                # header dictionary
        self.pagecount = None           # actual pages read from file (float)
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

  
        # read header and page packet
        header_packet = read_bin()

        # parse header
        parse_header(header_packet)

        # confirm number of pages read matches header
        check_pagecount()


    def view_data(self, start = 1, end = 900, temperature = True,
                  calibrate = True, update = True):

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

        # check whether data has been read
        if not self.header or self.data_packet is None or self.pagecount is None:
            print('****** WARNING: Cannot view data because file has not',
                  'been read.')
            return

        # store passed arguments before checking and modifying
        oldstart = start
        oldend = end

        # check start and end for acceptable values
        if start < 1: start = 1
        elif start > self.pagecount: start = round(self.pagecount)

        if end < start: end = start
        elif end > self.pagecount: end = round(self.pagecount)
        
        # initialize dataview
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
            lux = int(self.header['Lux'])
            volts = int(self.header['Volts'])
            
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
                    light = light * lux / volts

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

        # update object attributes
        if update:
            self.dataview_start = start
            self.dataview_end = end
            self.dataview = dt.Frame(dataview)

        # display message if start and end values were changed
        if oldstart != start or oldend != end:
            print('****** WARNING: Start or end values were modified to fit',
                  'acceptable range.\n',
                  f'       Old range: {oldstart} to {oldend}\n',
                  f'       New range: {start} to {end}.\n')

        return dataview

        
    def create_pdf(self, pdf_folder, window_hours = 4):

        '''create a pdf summary of this GENEActiv .bin file'''

        # check whether data has been read
        if not self.header or self.data_packet is None or self.pagecount is None:
            print('****** WARNING: Cannot view data because file has not',
                  'been read.')
            return

        # FILE NAMES AND PATHS -----------------
        
        bin_file = os.path.basename(self.file_path)

        base_file = os.path.splitext(bin_file)[0]

        pdf_file = base_file + '.pdf'
        pdf_path = os.path.join(pdf_folder, pdf_file)

        png_folder = os.path.join(pdf_folder, 'temp','')

        # calculate sample rate and pages per plot
        sample_rate = int(self.header['Measurement Frequency'][:-3])
        window_pages = round((window_hours * 60 * 60 * sample_rate) / 300)
        window_sequence = range(1, round(self.pagecount), window_pages)

        # *******Adjust hours if not even number of pages


        # CREATE PLOTS ------

        ###### THESE SETTINGS BELOW SHOULD BE MORE DYNAMIC#####

        # set axis limits for each plot [xmin, xmax, ymin, ymax]
        axis_lim = [[0, window_pages * 300, -8.2, 8.2],
                    [0, window_pages * 300, -8.2, 8.2],
                    [0, window_pages * 300, -8.2, 8.2],
                    [0, window_pages * 300, 0, 5000],
                    [0, window_pages * 300, 0, 1],
                    [0, window_pages * 300, 0, 40]]

        axis_yticks = [[-8,0,8],
                       [-8,0,8],
                       [-8,0,8],
                       [0,5000],
                       [0,1],
                       [0,40]]

        axis_ylabel = ['g', 'g', 'g', 'lux', '', 'deg C']

        axis_colour = ['b', 'g', 'r', 'c', 'm', 'y']

        plt.rcParams['lines.linewidth'] = 0.5
        plt.rcParams['figure.figsize'] = (6, 7.5)




        if not os.path.exists(png_folder): os.mkdir(png_folder)

        for start_index in window_sequence:

            fig, ax = plt.subplots(6, 1)
            fig.suptitle('PUT TIME RANGE HERE')

            end_index = start_index + window_pages - 1

            plot_data = self.view_data(start = start_index,
                                       end = end_index,
                                       update = False)

            
            

            subplot_index = 0

            for key in plot_data.keys():
                
                ax[subplot_index].spines["top"].set_visible(False)
                ax[subplot_index].spines["bottom"].set_visible(False)
                ax[subplot_index].spines["right"].set_visible(False)

                ax[subplot_index].axis(axis_lim[subplot_index])
                ax[subplot_index].get_xaxis().set_visible(False)

                ax[subplot_index].set_yticks(axis_yticks[subplot_index])
                ax[subplot_index].set_ylabel(axis_ylabel[subplot_index])

                ax[subplot_index].text(0.01, 0.9, key,
                                       color = axis_colour[subplot_index],
                                       transform = ax[subplot_index].transAxes)
                ax[subplot_index].plot(range(len(plot_data[key])),
                                       plot_data[key],
                                       color = axis_colour[subplot_index])

                subplot_index += 1

            png_file = 'plot_' + str(start_index) + '.png'
            
            fig.savefig(os.path.join(png_folder, png_file))
            plt.close(fig)


        # CREATE PDF ------

        # HEADER PAGE ----------------

        # initialize pdf
        pdf = fpdf.FPDF(format = 'letter')

        # add page and set font
        pdf.add_page()
        pdf.set_font("Courier", size = 16)

        # print file_name as header
        pdf.cell(200, 10, txt = bin_file, ln = 1, align = 'C', border = 0)

        pdf.set_font("Courier", size = 12)
        header_text = '\n'

        # find lenght of longest key in header
        key_length = max(len(key) for key in self.header.keys()) + 1

        # create text string for header information
        for key, value in self.header.items():
            header_text = header_text + f"{key:{key_length}}:  {value}\n"

        # print header to pdf
        pdf.multi_cell(200, 5, txt = header_text, align = 'L')



        # PLOT DATA PAGE -------------


        ###### PLOTING PLOTS IN WRONG ORDER BC FILE NAMES

        png_files = os.listdir(png_folder)

        for png_file in png_files:

            png_path = os.path.join(png_folder, png_file)

            # add page and set font
            pdf.add_page()
            pdf.set_font("Courier", size = 16)

            # print file_name as header
            pdf.cell(0, txt = bin_file, align = 'C')
            pdf.ln()

            pdf.image(png_path, x = 1, y = 15, type = 'png')


        shutil.rmtree(png_folder)

    

        # output to pdf file
        pdf.output(pdf_path)
                                     

        return pdf_path
