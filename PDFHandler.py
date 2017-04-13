import re
from PyPDF2 import PdfFileReader

class PDFHandler():
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

    # Read PDF file
    document = PdfFileReader(file(self.input_file, "rb"))
    num_pages = document.getNumPages()

    character_states_json = []

    pages_text = ""
    print "Reading PDF Pages ..."
    for num in range(num_pages):
      state = document.getPage(num).extractText()
      pages_text = pages_text + state


    # TODO: CHECK IF BELOW REGEX STATISFYS THIS AS WELL
    # ==== ==== ==== ==== ==== ==== ==== ==== ==== ====

    # Regex to pull out data pieces
    character_number = re.match('^\d+.', pages_text)
    character_desc   = re.match('^\d+.\s([A-Za-z,. \([0-9]).*[:|;]', pages_text)
    state_descriptions = re.findall(r"(?<=state\s\d\,)([A-Za-z, ]* [0-9]*.[0-9]*\s?[A-Za-z]*)", pages_text)

    if character_number and character_desc and state_descriptions:
      
      character_states_json.append({
        "number": character_number.group(0),
        "description": character_desc.group(0).replace(character_number.group(0), ''),
        "state_descriptions": state_descriptions.group()
      })

    else:

      # match state descriptions 
      st_desc = re.findall(r"(?::)([^.]*.)", pages_text)   
      st_desc.reverse()

      # matches column number and character label
      matches = re.findall(r"(\(?\d+[)|.][^.]*:)", pages_text)
      if matches:

        for m in matches:
          number = re.search('\d+', m)
          description = re.search('([A-Za-z ]+)', m)
          state_description = st_desc.pop()

          character_states_json.append({
            "number": int(number.group(0)),
            "description": str(description.group()),
            "state_descriptions": str(state_description)
          })


    print "returning PDF Character States"
    return character_states_json 
