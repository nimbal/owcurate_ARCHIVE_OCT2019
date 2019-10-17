# ENSURE COMPUTER DOES NOT GO TO SLEEP WHILE SCRIPT IS RUNNING


import sys
sys.path.append('/Users/kbeyer/repos')

import os
import re
import owcurate.Python.file.GENEActivFile as ga
import time
from pprint import pprint

# set folder paths
bin_folder = ('/Users/kbeyer/repos/test_data/testin')
pdf_folder = ('/Users/kbeyer/repos/test_data/testout/')

# list bin files in folder
bin_files = os.listdir(bin_folder)
bin_files = [file for file in bin_files if file.endswith('.bin')]

# list pdf files in folder
pdf_files = os.listdir(pdf_folder)
pdf_files = [file for file in pdf_files if file.endswith('.pdf')]

# check for bin files not in pdf files
bin_files = [bin_file for bin_file in bin_files
             if os.path.splitext(bin_file)[0] not in
             [os.path.splitext(pdf_file)[0] for pdf_file in pdf_files]]

# build full path to bin files
bin_paths = [os.path.join(bin_folder, bin_file) for bin_file in bin_files]

# count files and print message
num_files = len(bin_paths)
file_text = 'file' if num_files == 1 else 'files'
print(f'Creating {num_files} pdf summary {file_text} ...\n')

print('****** ENSURE COMPUTER DOES NOT SLEEP WHILE SCRIPT IS RUNNING ******\n')

# initialize file and time counters
file_count = 1
start = time.time()

# loop through bin files
for bin_path in bin_paths:

    print(f'File {file_count}\n',
          '---------------\n',
          f'{bin_path}',
          sep = '')


    # initialize bin file object    
    ga_file = ga.GENEActivFile(bin_path)

    # read bin file
    print(f'Reading file ...')
    ga_file.read()

    # create pdf cummary
    print('Creating pdf ...')
    ga_file.create_pdf(pdf_folder)

    # get time difference
    end = time.time()
    time_diff = end - start

    # calculate elapsed and estimate remaining time
    elapsed = time.strftime('%H:%M:%S', time.gmtime(time_diff))
    remaining = time.strftime('%H:%M:%S',
                              time.gmtime((time_diff / file_count) *
                                          (num_files - file_count)))

    print(f'{file_count} of {num_files} completed. \n',
          f'Elapsed time:    {elapsed}\n',
          f'Remaining time: ~{remaining}\n',
          sep = '')

    # increment file counter
    file_count += 1



