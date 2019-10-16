# Create a class called EDFFile for interacting with European Data Format files.
# - Specs for structure of EDF files are on the website edfplus.info
# - object should be initialized with an abolute path to a single file
# - attributes of the object will likely include:
#   - file path
#   - general header information from the file
#   - signal header information
#   - data from the signals stored in the file (for a specified window or the
#       entire file)
#   - information about the data such as some refernce to the start and end
#       points of the data currently stored in the object, the sample rate of
#       the data being stored (it may have been downsampled, etc.)
# - public methods should include methods to read the header information,
#       read either all of the data or a subset of the data, create a summary
#       pdf of the data


class EDFFile:

    '''Class for interacting with European Data Format Files (.edf) files.'''
    

    def __init__(self, file_path):

  

    def read_header(self, ...):

   
    def read_data(self, ...):

 
        
    def create_pdf(self, ...):

 
