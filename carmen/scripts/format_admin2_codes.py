# This script is used to format the admin2CodesASCII.txt file from Geonames
# before reading it into PostgreSQL.

import sys

input_filename  = '../../geonames_data/admin2CodesASCII.txt'
output_filename = '../../geonames_data/admin2Codes.txt'

input_file  = open(input_filename, 'r')
output_file = open(output_filename, 'w')

for line in input_file:
    new_line = line.replace(".", "\t", 2)
    tokens   = new_line.split("\t")
    del tokens[2]
    new_line  = "\t".join(tokens)
    output_file.write(new_line)

input_file.close()
output_file.close()