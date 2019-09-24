# This script is used to format the admin1CodesASCII.txt file from Geonames
# before reading it into PostgreSQL.

import sys

input_filename  = '../../geonames_data/admin1CodesASCII.txt'
output_filename = '../../geonames_data/admin1Codes.txt'

input_file  = open(input_filename, 'r')
output_file = open(output_filename, 'w')

for line in input_file:
    new_line = line.replace(".", "\t", 1)
    output_file.write(new_line)

input_file.close()
output_file.close()