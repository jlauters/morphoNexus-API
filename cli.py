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
 p.add_option('--output_file', '-o', default="matrix.nex")
 p.add_option('--counts', '-c', default=True, action="callback", callback=do_counts, help="return row and column counts for <input_file>" )

 options, arguments = p.parse_args()
 print 'reading input_file %s ...' % options.input_file
 
 if hasattr(options, 'rows'):
   print "File contained %d rows and %d columns" % (options.rows, options.cols)


 # TODO: Parse Matrix, pass optional supplied output filename
 mediator = matrixMediator( options.input_file )
 output_file = mediator.detectHandler( options.input_file )


 # Rename generated file to user supplied file
 os.rename( output_file, options.output_file )


 print '... writing generated matrix to  %s' % options.output_file

if __name__ == '__main__':
  main()
