import codecs
import nexus
from nexus import NexusReader
from matrix_utils import verifyTaxa

class NexusHandler():
  """ Nexus File Type implementation of matrix handling needs """

  input_file = None
  ncols = 0
  nrows = 0
  custom_block = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):

    # If we have a nexus file already, we should verify the taxa and add custom block,
    # do any syntax cleanup needed to get Mesquire to parse without error.

    try:
      nr = NexusReader(self.input_file)

    except nexus.reader.NexusFormatException, e:
      taxa_nums = []
      parts = str(e).split('(')
      for part in parts:

        mini_parts = part.split(')')
        part = mini_parts[0]

        if part.replace(')', '').isdigit():
          print part.replace(')', '')
          taxa_nums.append( int(part.replace(')','')) )

      
      filedata = None
      with open(self.input_file, 'r') as file: 
        filedata = file.read()

      # TODO: dataype=mixed(type:range, type2:range2) cannot be read by mesquite but MrBayes can read/write mixed datatype matrices
      filedata = filedata.replace("NTAX=" + str(taxa_nums[1]), "NTAX=" + str(taxa_nums[0]) )
      filedata = filedata.replace("symbol=", "symbols=")
      filedata = filedata.replace("inter;", "interleave;")

      with open(self.input_file, 'w') as file:
        file.write(filedata)

      return False
    

    self.nrows = nr.data.ntaxa

    custom_block = "\n\nBEGIN VERIFIED_TAXA;\n"
    custom_block += "Dimensions ntax=" + str(self.nrows) + " nchar=4;\n"

    for tax in nr.data.taxa:
    
      verified_taxa = verifyTaxa(tax)
      verified_name = None

      if verified_taxa:
        for taxa in verified_taxa:
          verified_name = taxa['name_string'].lower()
          custom_block += tax + "    " + taxa['name_string'] + "    " + taxa['match_value'] + "    " + taxa['datasource'] + "\n"
      else:
        custom_block += tax + "\n"

    custom_block += ";\n"
    custom_block += "END;\n\n"

    self.custom_block = custom_block

    # keep the upload path and filename, but change extension
    file_parts = self.input_file.split('.')
    output_file = file_parts[0] + '.nex'

    ### Simple Append to end of file ####
    nexus_file = codecs.open(output_file, 'a', 'utf-8')
    nexus_file.write(self.custom_block)
    nexus_file.close()

    return output_file
