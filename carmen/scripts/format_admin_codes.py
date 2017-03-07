import sys

input_filename  = '../data/dump/admin1CodesASCII.txt'
output_filename = '../data/dump/admin1Codes.txt'

input_file  = open(input_filename, 'r')
output_file = open(output_filename, 'w')

for line in input_file:
    new_line = line.replace(".", "\t", 1)
    output_file.write(new_line)

input_file.close()
output_file.close()