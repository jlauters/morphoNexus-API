import re
import codecs
from docx import Document
from matrix_utils import verifyTaxa, is_number

class DocxHandler():
  """ Docx File Type implementation of matrix handling needs """

  input_file = None
  ncols = 0
  nrows = 0
  custom_block = None

  def __init__(self, input_file):
    self.input_file = input_file
  
  @staticmethod
  def clean_paragraphs(paragraphs):
  
    cleaned_states = []
    prog = re.compile('^\d')
    is_current = False
    current_state = ""

    for p in paragraphs:
    
      if prog.match(p.text):
        is_current = True

      if is_current and p.text:
        current_state = current_state + p.text
      else:
        if current_state:
          cleaned_states.append( current_state )

        is_current = False
        current_state = ""

    return cleaned_states



  def read_file(self):

    # Read Docx file
    document = Document(self.input_file)
    character_states = DocxHandler.clean_paragraphs( document.paragraphs )

    character_states_json = []
    # Cleaned Character States
    for state in character_states:
      print state

      # Regex to pull out data pieces
      character_number = re.match('^\d+.', state)
      character_desc   = re.match('^\d+.\s([A-Za-z,. \([0-9]).*[:|;]', state)
      state_descriptions = re.findall(r"(?<=state\s\d\,)([A-Za-z, ]* [0-9]*.[0-9]*\s?[A-Za-z]*)", state)

      print "character number: " + str(character_number.group(0))
      print "character desc: " + str(character_desc.group(0).replace(character_number.group(0), '').encode('utf8'))
      print "character state desc: "
      print state_descriptions
      print "========================"

      character_states_json.append({
        "number": character_number.group(0),
        "description": character_desc.group(0).replace(character_number.group(0), ''),
        "state_descriptions": state_descriptions
      })


    return character_states_json 
