import re
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
  nr = None

  def __init__(self, input_file):
    self.input_file = input_file

  def read_file(self):

    # If we have a nexus file already, we should verify the taxa and add custom block,
    # do any syntax cleanup needed to get Mesquire to parse without error.

    print "top of read_file"

    taxa_nums = []
    try:
      print "creating nexus reader ... "
      nr = NexusReader(self.input_file)
      self.nr = nr


    except nexus.reader.NexusFormatException, e:
      print "Nexus Format Exception: "
      print e

      if str(e).strip() == "Duplicate Block mrbayes":
        # Remove duplicate block      
        filedata = None
        with open(self.input_file, 'r') as file: 
          filedata = file.read()
 
        mrbayes_data = re.search('(?<=begin mrbayes;)(?s)(.*)(?=end;)', filedata.lower())

        replace_line = "begin mrbayes;\n" + mrbayes_data.group(0) + "end;\n"
 
        insensitive_replace = re.compile(re.escape('begin mrbayes;'), re.IGNORECASE)
        insensitive_replace = insensitive_replace.sub('', replace_line) 

        insensitive_replace_again = re.compile(re.escape('end;'), re.IGNORECASE)
        insensitive_replace = insensitive_replace_again.sub('', insensitive_replace)

        filedata = re.sub('(?<=Begin Mrbayes;)(?s)(.*)(?=END;)', '', filedata)
        filedata = re.sub('Begin Mrbayes;END;', '', filedata)

        filedata = filedata + "BEGIN MRBAYES;\n" + insensitive_replace + "\nEND;\n"

        with open(self.input_file, 'w') as file:
          file.write(filedata)
      
        print "Trying again"
        # try again?
        self.read_file()

      else:
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
          file.close()
    
    print "After Try/Catch"

    if self.nr is None:
      print "nr isn't set ... "


    self.nrows = self.nr.data.ntaxa

    custom_block = "\n\nBEGIN VERIFIED_TAXA;\n"
    custom_block += "Dimensions ntax=" + str(self.nrows) + " nchar=4;\n"

    for tax in self.nr.data.taxa:
    
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
