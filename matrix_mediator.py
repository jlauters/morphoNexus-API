import os
from NexusHandler import NexusHandler
from XlsHandler import XlsHandler
from TxtHandler import TxtHandler
from DocxHandler import DocxHandler
from PDFHandler import PDFHandler

class matrixMediator:
  matrixHandler = None

  def __init__(self, input_file, character_file=''):
    #self.detectHandler(input_file)
    pass 

  def getCounts(self, input_file):

    counts = {"rows": 0, "cols": 0}
    if os.path.isfile(input_file):
      filename, file_extension = os.path.splitext(input_file)

      if ".xlsx" == file_extension or ".xls" == file_extension:
        self.matrixHandler = XlsHandler(input_file)
        counts = self.matrixHandler.getCounts()

    return counts

  def detectHandler(self, input_file, character_file=''):

    character_descriptions = []
    if character_file and os.path.isfile(character_file):

      print "Charfile found"

      # Parse Charatcer File for column names, and state labels 
      char_filename, char_extension = os.path.splitext(character_file) 
      if ".docx" == char_extension:
        self.matrixHandler = DocxHandler(character_file)
        character_descriptions = self.matrixHandler.read_file()

      if ".pdf" == char_extension:
        self.matrixHandler = PDFHandler(character_file)
        character_descriptions = self.matrixHandler.read_file()

      if ".txt" == char_extension:
        character_descriptions = TxtHandler.read_charfile( character_file )

    # Parse Matrix file and conform to nexus file structure
    if os.path.isfile(input_file):
      filename, file_extension = os.path.splitext(input_file)

      print "input file type: "
      print file_extension

      if ".nex" == file_extension:
        self.matrixHandler = NexusHandler(input_file, character_descriptions)
        output_file = self.matrixHandler.read_file()
        return output_file

      elif ".xlsx" == file_extension or ".xls" == file_extension:
        self.matrixHandler = XlsHandler(input_file, character_descriptions)
        output_file = self.matrixHandler.read_file()
        return output_file

      elif ".txt" == file_extension:
        self.matrixHandler = TxtHandler(input_file, character_descriptions)
        output_file = self.matrixHandler.read_file()
        return output_file

      else:
        print "unknown filetype found."
        print input_file
    else:
      print "input file not found"
