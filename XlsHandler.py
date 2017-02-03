import codecs
import xlrd
from matrix_utils import verifyTaxa, is_number
from nexus import NexusWriter

class XlsHandler():
  """ Xls(x) File Type implementation of matrix handling needs """

  input_file = None
  ncols = 0
  nrows = 0
  custom_block = None

  def __init__(self, input_file):
    self.input_file = input_file
    self.read_file()

  def read_file(self):

    book = xlrd.open_workbook(input_file)
    sh = book.sheet_by_index(0)

    nw = NexusWriter()

    self.nrows = sh.nrows
    self.ncols = sh.ncols

    nw.add_comment("Morphobank generated Nexus File")
  
    custom_block = "\n\nBEGIN VERIFIED_TAXA;\n"
    custom_block += "Dimensions ntax=" + str(self.nrows) + " nchar=4;\n"

    # Species List Taxa
    for rx in range(self.nrows):
      if rx:
    
        taxon_name = str(sh.cell_value(rowx=rx, colx=0)).strip()
   
        verified_taxa = verifyTaxa(taxon_name)
        verified_name = None
        
        if verified_taxa:
          for taxa in verified_taxa:
            verified_name = taxa['name_string'].lower()
            custom_block += taxon_name + "    " + taxa['name_string'] + "    " + taxa['match_value'] + "    " + taxa['datasource'] + "\n"
        else:
          custom_block += taxon_name + "\n"
    
        for cx in range(self.ncols):
          if cx:

            if is_number( sh.cell_value(rowx=rx, colx=cx)):
              cell_value = int(sh.cell_value(rowx=rx, colx=cx))
            else:
              cell_value = sh.cell_value(rowx=rx, colx=cx)
              cell_value = cell_value.replace("{", "(")
              cell_value = cell_value.replace("}", ")")

            if verified_name:
              nw.add(verified_name, cx, cell_value)
            else:
              nw.add(taxon_name, cx, cell_value)
  
    custom_block += ";\n"
    custom_block += "END;\n"

    self.custom_block = custom_block

    nw.write_to_file(filename='output.nex', interleave=False, charblock=False)

    ## quick append Custom Block 
    nexus_file = open('output.nex', 'a')
    nexus_file.write(custom_block)
    nexus_file.close()


