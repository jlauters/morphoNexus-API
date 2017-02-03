import os
from NexusHandler import NexusHandler
from XlsHandler import XlsHandler
from TxtHandler import TxtHandler

class matrixMediator:
  matrixHandler = None

  def __init__(self, input_file):
    self.detectHandler(input_file)

  def detectHandler(self, input_file):
  
    print "in detectHandler. checking input file"
    
    if os.path.isfile(input_file):
      filename, file_extension = os.path.splitext(input_file)

      if ".nex" == file_extension:
        self.matrixHandler = NexusHandler(input_file)

      elif ".xlsx" == file_extension or ".xls" == file_extension:
        self.matrixHandler = XlsHandler(input_file)

      elif ".txt" == file_extension:
        self.matrixHandler = TxtHandler(input_file)

      else:
        print "unknown filetype found."
        print input_file
