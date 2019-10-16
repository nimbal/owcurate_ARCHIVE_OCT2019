# Authors: Kit Beyer with code/ideas borrowed from David Ding and Kyle Weber
# Date: September 2019

import os
import shutil
import datetime
import fpdf
import matplotlib.pyplot as plt
import matplotlib.style as mstyle
import matplotlib.dates as mdates

mstyle.use('fast')


class GENEActivFile:

    '''Class for interacting with GENEActiv .bin data files.


        Attributes
        ----------
        file_path : str
            the path to the GENEActiv .bin file
        header : dict
            keys and values from the file header
        pagecount : float
            number of actual pages read from the file
        pagecount_match : bool
            does the pagecount match the 'Number of Pages' in the header
        data_packet : str (hex)
            hexadecimal string of the complete data from the file
        dataview_start : int
            start page of current dataview
        dataview_end : int
            end page of current dataview
        dataview_sample_rate : float
            somple rate of current dataview
        dataview = dict
            current dataview, one item for each signal

        Methods
        -------
        read()
            reads and parses header and reads hexidecimal string of data
            
        view_data(start = 1, end = 900, downsample = 1, temperature = True,
                  calibrate = True, update = True)
            parses a window of hexidecimal data previously read from
            the file for viewing
                  

        create_pdf(pdf_folder, window_hours = 4, downsample = 5)
            creates a pdf summary of the file


    '''
    

    def __init__(self, file_path):

        # TODO:
        # - decide on best way of storing dataview (dictionary, numpy, pandas, datatable?)

        '''
        Parameters
        ----------
        file_path : str
            path to the GENEActiv .bin file
        '''

        self.file_path = file_path       # path to .bin file
        self.header = {}                 # header dictionary
        self.pagecount = None            # actual pages read from file (float)
        self.pagecount_match = None      # does pagecount read match header
        self.accel_x_min = None          # accelerometer x minimum value
        self.accel_x_max = None          # accelerometer x maximum value
        self.accel_y_min = None          # accelerometer y minimum value
        self.accel_y_max = None          # accelerometer y maximum value
        self.accel_z_min = None          # accelerometer z minimum value
        self.accel_z_max = None          # accelerometer z maximum value
        self.light_min = None            # light minimum value
        self.light_max = None            # light maximum value
        self.data_packet = None          # hexadecimal data from entire file
        self.dataview_start = None       # start page of current dataview
        self.dataview_end = None         # end page of current dataview
        self.dataview_sample_rate = None # sample rate of current dataview
        self.dataview = None             # current dataview (subset of data)
        

    def read(self):

        '''reads text header and hex data from GENEActiv .bin file

        Parameters
        ----------
        None

        Returns
        -------
        bool
            True if file exists and was read, False if file does not exist
        
        '''

        def read_bin():

            '''reads text lines from a GENEActiv .bin file

            Parameters
            ----------
            None
            
            Returns
            -------
            list
                one string item per line in the header'''

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

            '''parses the header packet previously read from the file

            Stores the header information in the header (dict) attribute.

            Parameters
            ----------
            header_packet : list
                one string item per line in the header

            Returns
            -------
            None

            '''

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

            '''Checks to see if number of actual pages read matches header

            Parameters
            ----------
            None

            Returns
            -------
            None

            '''

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

        def calc_ranges():

            '''Calculates actual accelerometer min and max values

            Parameters
            ----------
            None

            Returns
            -------
            None

            '''

            self.accel_x_min = ((-204800 - int(self.header['x offset'])) /
                                int(self.header['x gain']))

            self.accel_y_min = ((-204800 - int(self.header['y offset'])) /
                                int(self.header['y gain']))

            self.accel_z_min = ((-204800 - int(self.header['z offset'])) /
                                int(self.header['z gain']))

            self.accel_x_max = ((204700 - int(self.header['x offset'])) /
                                int(self.header['x gain']))

            self.accel_y_max = ((204700 - int(self.header['y offset'])) /
                                int(self.header['y gain']))

            self.accel_z_max = ((204700 - int(self.header['z offset'])) /
                                int(self.header['z gain']))

            self.light_min = (0 * int(self.header['Lux']) /
                              int(self.header['Volts']))

            self.light_max = (1023 * int(self.header['Lux']) /
                              int(self.header['Volts']))

            


        # if file exists then read it
        if os.path.exists(self.file_path):
            
            # read header and page packet
            header_packet = read_bin()

            # parse header
            parse_header(header_packet)

            # confirm number of pages read matches header
            check_pagecount()

            # calculate accelerometer ranges
            calc_ranges()

            return True # file exists and was read

        else:

            print(f"****** WARNING: {self.file_path} does not exist.\n")

            return False # file did not exist


    def view_data(self, start = 1, end = -1, downsample = 1,
                  temperature = True, calibrate = True, update = True):

        #TO DO:
        # - test to ensure values are correct (compare to GENEAread R package)
        # - confirm dictionary item lengths equal ?
        # - option to adjust for clock drift (synchronize) - just adjust
        # actual sample rate based on clock drift ?
        # - start and end by time (find last page w page time < start)
        # - add option to return battery voltage??

        '''parses a subset of the data in the file for viewing

        Updates the dataview attributes with values pertaining to the current
        window of data (if update is set to True).

        Parameters
        ----------
        start : int
            start page of window (coerced to be > 0, default = 1)
        end : int
            end page of window (coerced to be between start and last page,
            default = -1 = read all pages)
        downsample : int
            factor by which to downsample (coerced into range: 1-6, default = 5) 
        temperature : bool
            parse temperature data? (default = True)
            NOTE: temperature is only sampled once per page but is currently
            inserted at each measurement consistent with GENEARead R package 
        calibrate : bool
            should accelerometer and light values be calibrated (default = True)
        update : bool
            should dataview attributes be updated? (default = True)

        Returns
        -------
        dataview : dict
            one item for each signal parsed
        '''

        def uint2int(unsigned_value, sign_bit):

            '''converts an unsigned integer (in two's complement
            representation) to a signed integer

            Parameters
            ----------
            unsigned_value : int
                unsigned integer value
            sign_bit : int
                the bit of the integer that indicates the sign (analagous to
                the intended size of the number in bits regardless of how it is
                actually stored)

            Returns
            -------
            signed_value : int
                signed integer value
            ''' 

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
        if (not self.header or self.data_packet is None
            or self.pagecount is None):

            print('****** WARNING: Cannot view data because file has not',
                  'been read.\n')
            return

        # store passed arguments before checking and modifying
        old_start = start
        old_end = end
        old_downsample = downsample

        # check start and end for acceptable values
        if start < 1: start = 1
        elif start > self.pagecount: start = round(self.pagecount)

        if end == -1 or end > self.pagecount: end = round(self.pagecount)
        elif end < start: end = start

        #check downsample for valid values
        if downsample < 1: downsample = 1
        elif downsample > 6: downsample = 6
        
        # initialize dataview
        dataview = {"time" : [],
                    "accel_x" : [],
                    "accel_y" : [],
                    "accel_z" : [],
                    "light"   : [],
                    "button"  : []}

        downsampled_rate = (int(self.header['Measurement Frequency'][:-3]) /
                            downsample)
        meas_per_page = int(300 / downsample)

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

        # grab chunk of page times from packet
        time_chunk = [self.data_packet[i]
                    for i in range((start - 1) * 10 + 3, end * 10, 10)]

        # loop through pages
        for time_line in time_chunk:

            # get page time
            colon = time_line.index(':')
            page_time = time_line[colon + 1:]
            page_time = datetime.datetime.strptime(page_time, '%Y-%m-%d %H:%M:%S:%f')

            # generate timestamps
            times = [page_time + datetime.timedelta(seconds = i / downsampled_rate)
                      for i in range(meas_per_page)]
            #times = [t.strftime('%Y-%m-%d %H:%M:%S.%f') for t in times]

            dataview['time'].extend(times)      
            

        # grab chunk of data from packet
        data_chunk = [self.data_packet[i]
                    for i in range((start - 1) * 10 + 9, end * 10, 10)]
        
        # loop through pages
        for data_line in data_chunk:

            # loop through 300 measurements in each page
            for meas_index in range(0, 300, downsample):

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
                dataview['temp'].extend(
                    [float(temp_line[colon + 1:])] * round(meas_per_page))

        # update object attributes
        if update:
            self.dataview_start = start
            self.dataview_end = end
            self.dataview_sample_rate = downsampled_rate
            self.dataview = dataview

        # display message if start and end values were changed
        if old_start != start or old_end != end:
            print('****** WARNING: Start or end values were modified to fit',
                  'acceptable range.\n',
                  f'       Old range: {old_start} to {old_end}\n',
                  f'       New range: {start} to {end}\n')

        # display message downsample ratio was changed
        if old_downsample != downsample:
            print('****** WARNING: Downsample value was modified to fit',
                  'acceptable range.\n',
                  f'       Old value: {old_downsample}\n',
                  f'       New value: {downsample}\n')

        return dataview

        
    def create_pdf(self, pdf_folder, window_hours = 4, downsample = 5):

        # TODO:
        # - DOUBLES PLOT TIME TO ADD DATES AS DATETIME TYPE

        '''creates a pdf summary of the file


        Parameters
        ----------
        pdf_folder : str
            path to folder where pdf will be stored
        window_hours : int
            number of hours to display on each page (default = 4) -- if hour occurs
            in the middle of a data page then time displayed on each pdf page may
            be slightly less than the number of hours specified
        downsample : int
            factor by which to downsample (range: 1-6, default = 5)

        Returns
        -------
        pdf_path : str
            path to pdf file created

        '''

        # check whether data has been read
        if not self.header or self.data_packet is None or self.pagecount is None:
            print('****** WARNING: Cannot view data because file has not',
                  'been read.')
            return

        # get filenames and paths     
        bin_file = os.path.basename(self.file_path)

        base_file = os.path.splitext(bin_file)[0]

        pdf_file = base_file + '.pdf'
        pdf_path = os.path.join(pdf_folder, pdf_file)

        png_folder = os.path.join(pdf_folder, 'temp','')

        # calculate sample rate and pages per plot
        sample_rate = int(self.header['Measurement Frequency'][:-3])
        window_pages = round((window_hours * 60 * 60 * sample_rate) / 300)
        window_sequence = range(1, round(self.pagecount), window_pages)


        # CREATE PLOTS ------

        # define date locators and formatters
        hours = mdates.HourLocator()
        hours_fmt = mdates.DateFormatter('%H:%M')

        # set plot parameters


        # each accel axis has a different min and max based on the digital range
        # and the offset and gain values (-8 to 8 stated in the header is just
        # a minimum range, actual range is slightly larger)

        accel_min = min([self.accel_x_min, self.accel_y_min, self.accel_z_min])
        accel_max = max([self.accel_x_max, self.accel_y_max, self.accel_z_max])        
        accel_range = accel_max - accel_min
        accel_buffer = accel_range * 0.1

        light_min = self.light_min
        light_max = self.light_max

        light_range = light_max - light_min
        light_buffer = light_range * 0.1
                        
        yaxis_lim = [[accel_min - accel_buffer, accel_max + accel_buffer],
                    [accel_min - accel_buffer, accel_max + accel_buffer],
                    [accel_min - accel_buffer, accel_max + accel_buffer],
                    [light_min - light_buffer, light_max + light_buffer],
                    [-0.01, 1],
                    [9.99, 40.01]]

        yaxis_ticks = [[-8, 0, 8],
                       [-8, 0, 8],
                       [-8, 0, 8],
                       [0, 10000, 20000, 30000],
                       [0, 1],
                       [10, 20, 30, 40]]

        yaxis_units = [self.header['Accelerometer Units'],
                       self.header['Accelerometer Units'],
                       self.header['Accelerometer Units'],
                       self.header['Light Meter Units'],
                       '',
                       self.header['Temperature Sensor Units']]

        yaxis_lines = [[self.accel_x_min, 0, self.accel_x_max],
                       [self.accel_y_min, 0, self.accel_y_max],
                       [self.accel_z_min, 0, self.accel_z_max],
                       [light_min, light_max]]
                       

        line_color = ['b', 'g', 'r', 'c', 'm', 'y']

        plt.rcParams['lines.linewidth'] = 0.25
        plt.rcParams['figure.figsize'] = (6, 7.5)
        plt.rcParams['figure.subplot.top'] = 0.92
        plt.rcParams['figure.subplot.bottom'] = 0.06
        plt.rcParams['font.size'] = 8

        # create temp folder to store .png files
        if not os.path.exists(png_folder): os.mkdir(png_folder)

        # loop through time windows to create separate plot for each
        for start_index in window_sequence:

            # get data for current window
            end_index = start_index + window_pages - 1
            plot_data = self.view_data(start = start_index,
                                       end = end_index,
                                       downsample = downsample,
                                       update = False)

            # format start and end date for current window
            time_format = '%b %-d, %Y (%A) @ %H:%M:%S.%f'
            window_start = plot_data['time'][0]
            window_start_txt = window_start.strftime(time_format)[:-3]

            window_end = plot_data['time'][-1]
            window_end_txt = window_end.strftime(time_format)[:-3]

            # initialize figure with subplots
            fig, ax = plt.subplots(6, 1)

            # insert date range as plot title
            fig.suptitle(f'{window_start_txt} to {window_end_txt}',
                         fontsize = 8, y = 0.96)

            # initialize subplot index
            subplot_index = 0

            # loop through subplots and generate plot
            for key in list(plot_data.keys())[1:]:

                # plot signal
                ax[subplot_index].plot(plot_data['time'],
                                       plot_data[key],
                                       color = line_color[subplot_index])
                
                # remove box around plot
                ax[subplot_index].spines['top'].set_visible(False)
                ax[subplot_index].spines['bottom'].set_visible(False)
                ax[subplot_index].spines['right'].set_visible(False)

                # set axis ticks and labels
                ax[subplot_index].xaxis.set_major_locator(hours)
                ax[subplot_index].xaxis.set_major_formatter(hours_fmt)
                if subplot_index != 5:
                    ax[subplot_index].set_xticklabels([])

                ax[subplot_index].set_yticks(yaxis_ticks[subplot_index])
                units = yaxis_units[subplot_index]
                ax[subplot_index].set_ylabel(f'{key} ({units})')


                # set vertical lines on plot at hours
                ax[subplot_index].grid(True, 'major', 'x',
                                       color = 'k', linestyle = '--')

                # set horizontal lines on plot at zero and limits
                if subplot_index < 4:
                    for yline in yaxis_lines[subplot_index]:
                        ax[subplot_index].axhline(y = yline, color = 'grey',
                                                  linestyle = '-')

                # set axis limits
                ax[subplot_index].set_ylim(yaxis_lim[subplot_index])
                ax[subplot_index].set_xlim(window_start,
                                           window_start +
                                           datetime.timedelta(hours = 4))

                # increment to next subplot
                subplot_index += 1

            # save figure as .png and close
            png_file = 'plot_' + f'{start_index:09d}' + '.png'
            fig.savefig(os.path.join(png_folder, png_file))
            plt.close(fig)


        # CREATE PDF ------

        # HEADER PAGE ----------------

        # initialize pdf
        pdf = fpdf.FPDF(format = 'letter')

        # add first page and print file name at top
        pdf.add_page()
        pdf.set_font("Courier", size = 16)
        pdf.cell(200, 10, txt = bin_file, ln = 1, align = 'C', border = 0)

        # set font for header info
        pdf.set_font("Courier", size = 12)
        header_text = '\n'

        # find length of longest key in header
        key_length = max(len(key) for key in self.header.keys()) + 1

        # create text string for header information
        for key, value in self.header.items():
            header_text = header_text + f"{key:{key_length}}:  {value}\n"

        # print header to pdf
        pdf.multi_cell(200, 5, txt = header_text, align = 'L')

        # PLOT DATA PAGES -------------

        # list all .png files in temp folder
        png_files = os.listdir(png_folder)
        png_files.sort()

        # loop through .png files to add to pdf
        for png_file in png_files:

            # create full .png file path
            png_path = os.path.join(png_folder, png_file)

            # add page and set font
            pdf.add_page()
            pdf.set_font("Courier", size = 16)

            # print file_name as header
            pdf.cell(0, txt = bin_file, align = 'C')
            pdf.ln()

            # insert .png plot into pdf
            pdf.image(png_path, x = 1, y = 13, type = 'png')

        # SAVE PDF AND DELETE PNGS --------------

        # save pdf file
        pdf.output(pdf_path)

        # delete temp .png files
        shutil.rmtree(png_folder)
                                     
        return pdf_path
