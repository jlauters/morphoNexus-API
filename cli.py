#!/user/bin/env python

import os
import optparse
from matrix_mediator import matrixMediator

# Get quick counts dict from XlsParser 
def do_counts(option, opt_str, value, parser):

    mediator = matrixMediator( parser.values.input_file )
    counts = mediator.getCounts( parser.values.input_file )

    parser.values.rows = counts['rows']
    parser.values.cols = counts['cols']

def main():

 p = optparse.OptionParser(description=' Pass an excel matrix file to be converted into nexus file format')
 p.add_option('--input_file', '-i')
 p.add_option('--character_file', '-C', help="file for when character names are not in main matrix file")
 p.add_option('--output_file', '-o', default="matrix.nex")
 p.add_option('--counts', '-c', default=True, action="callback", callback=do_counts, help="return row and column counts for <input_file>" )

 options, arguments = p.parse_args()
 
 if not options.input_file:
   p.error('Input file not given')

 # if counts flag is set, just return counts
 if hasattr(options, 'rows'):
   print "rows: %d, cols: %d" % (options.rows, options.cols)
 else:

   print 'reading input_file %s ...' % options.input_file

   if hasattr(options, 'character_file'):
     print 'handling case where character names are in a different file ...'

     mediator = matrixMediator( options.input_file, options.character_file)
     output_file = mediator.detectHandler( options.input_file, options.character_file )
   else:

     mediator = matrixMediator( options.input_file )
     output_file = mediator.detectHandler( options.input_file )
       
   # Rename generated file to user supplied file
   os.rename( str(output_file), str(options.output_file) )

   print '... writing generated matrix to  %s' % options.output_file

if __name__ == '__main__':
  main()
