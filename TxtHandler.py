import os
import time
import codecs
import numpy
from matrix_utils import verifyTaxa
from nexus import NexusWriter
from NexusHandler import NexusHandler

class TxtHandler():
  """ Txt File Type implementation of matrix handling needs """

  input_file = None
  first_line = None
  ncols = 0
  nrows = 0
  custom_block = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):
  
    with open( self.input_file, 'r') as f:
      self.first_line = f.readline()
   
      # TODO: Needs work xread / tnt file format is loose

      # xread has some other potential clues
      xread_filename = f.readline().strip().replace("'", "")
      xread_matrix_dimensions = f.readline()
      lines = f.readlines()

      f.close

    if "#NEXUS" == self.first_line.strip():
      print "text file is nexus"
  
      # move to nexus folder
      filename, file_extension = os.path.splitext(self.input_file)
      os.rename(self.input_file, filename + ".nex")

      # send to correct matrix handler
      # TODO: A little dirty, probably should 
      # change mediator's handler param so this flows cleaner
      matrixHandler = NexusHandler( filename + ".nex" )
      return matrixHandler.read_file()

    elif "xread" == self.first_line.strip():
    
      print "xread format found"

      dimensions = str(xread_matrix_dimensions).split(' ')
      self.ncols = int(dimensions[0])
      self.nrows = int(dimensions[1])

      custom_block = "\n\nBEGIN VERIFIED_TAXA;\n"
      custom_block += "Dimensions ntax=" + str(self.nrows) + " nchar=4;\n"

      matrix = ""
      matrix_arr = []
      line_buffer = ""
      row_taxa = []
      for l in lines:
        if ";proc/;" != l.strip():

          if line_buffer:
            line_row = line_buffer + " " + l.strip()
          else:
            line_row = l.strip()
        
          if len(line_row) >= self.ncols:
 
            # reconstitute broken rows, then remove space/tabbing
            line_parts = line_row.split(' ')
            line_parts = list(filter(None, line_parts))

            taxon_name = line_parts[0]
            taxon_chars = line_parts[1]
            #taxon_chars = line_parts[1].replace("[", "(")
            #taxon_chars = taxon_chars.replace("]", ")")
          
            #  verify taxa
            verified_taxa = verifyTaxa(taxon_name)
            verified_name = None

            if verified_taxa:
              for taxa in verified_taxa:

                # We split here to exclude the odd citation on the taxon name ( maybe regex what looks like name & name, year would be better )
                verified_name = taxa['name_string'].lower().split(' ')
                row_taxa.append( verified_name[0] )

                custom_block += taxon_name + "    " + taxa['name_string'] + "    " + taxa['match_value'] + "    " + taxa['datasource'] + "\n"

              matrix += "    " + verified_name[0] + "    " + taxon_chars.strip() + "\n"
              matrix_arr.append(taxon_chars.strip())
            else:

              row_taxa.append( taxon_name )
              custom_block += taxon_name + "\n"
              matrix += "    " + taxon_name + "    " + taxon_chars.strip() + "\n"
              matrix_arr.append(taxon_chars.strip())

            line_buffer = ""
          else:
            line_buffer += l.strip()

      custom_block += ";\n"
      custom_block += "END;\n"

      self.custom_block = custom_block      

      print "matrix array"
      marr = []
      for row in matrix_arr:
        items = list(row)
        marr.append(items)

      m = numpy.matrix(marr)
       
      nw = NexusWriter()
      nw.add_comment("Morphobank generated Nexus from xread .txt file ")

      for rx in range(self.nrows):
        taxon_name = row_taxa[rx] 
        cell_value = m.item(rx)

        for cindex, cv in enumerate(cell_value):
          char_no = cindex + 1
          nw.add(taxon_name, char_no, cv)


      # keep the upload path and filename, but change extension
      file_parts = self.input_file.split('.')
      output_file = file_parts[0] + '.nex'

      nw.write_to_file(filename=output_file, interleave=False, charblock=True)

      # move to nexus folder
      #os.rename(xread_filename + ".nex", "./nexus/" + xread_filename + ".nex")

      # wait for file to move before open and append
      #while not os.path.exists('./nexus/' + xread_filename + '.nex'):
      #  time.sleep(1)
 
      #if os.path.isfile('./nexus/' + xread_filename + '.nex'):

      # Custom Block Section
      nexus_file = codecs.open(output_file, 'a', 'utf-8')
      nexus_file.write(custom_block)
      nexus_file.close()      

      return output_file

    else:
      print "do not know how to process this .txt file"

