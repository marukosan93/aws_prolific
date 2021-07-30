import csv
import sys
import subprocess

#This script generated json files with 25 items to be written to DB, it also generates and executes a bash script to upload all of them together

INPUT_FILE = sys.argv[1]  #CSV file to be used as input
STUDY = sys.argv[2]  #Short string identifying the study in aws

with open(INPUT_FILE, newline='') as f:
    reader = csv.reader(f)
    data = list(reader)

first_row = data[0]
table_name = "Scenarios_DB_"+STUDY
filenamejson = "outputs/scenarios_db"
jsonappendix = ".json"
preamble_string = ""

preamble_string += "{\n"
preamble_string += "\""+table_name+"\": [\n"
final_string = ""
i = 0
count = 0
data = data[2:]
for cc, row in enumerate(data):
    #if len(row)>0:
    if count == 0:
        final_string = ""
    final_string += ","
    final_string += "{\n"
    final_string += "\"PutRequest\": {\n"
    final_string += "\"Item\": {\n"
    final_string += "\""+first_row[0]+"\": {\"S\":\""+row[0]+"\"},\n"
    final_string += "\""+first_row[1]+"\": {\"S\":\""+row[1]+"\"},\n"
    final_string += "\""+first_row[2]+"\": {\"S\":\""+row[2]+"\"},\n"
    final_string += "\""+first_row[3]+"\": {\"S\":\""+row[3]+"\"},\n"
    final_string += "\""+first_row[4]+"\": {\"S\":\""+row[4]+"\"},\n"
    final_string += "\""+first_row[5]+"\": {\"S\":\""+row[5]+"\"}\n"
    final_string += "}\n"
    final_string += "}\n"
    final_string += "}\n"
    count += 1
    if count > 24 or cc == len(data)-1:
        final_string += "]\n"
        final_string += "}\n"
        count = 0
        i += 1
        with open(filenamejson+str(i)+jsonappendix, 'w') as outfile:
            outfile.write(preamble_string+final_string[1:])
            outfile.close()

string_sh_script = ""
first_line_sh_file ="\#!/bin/sh\n"
for num in range(1,i+1):
    perc = int((num/i)*100)
    perc = str(perc)
    string_sh_script+="aws dynamodb batch-write-item --request-items file://outputs/scenarios_db"+str(num)+".json\n"
    string_sh_script+="echo \"Writing to DB - "+perc+"%"+"\"\n"
with open("outputs/load_scenarios_in_DB.sh", 'w') as outfile:
    outfile.write(first_line_sh_file+string_sh_script)
    outfile.close()
line = string_sh_script[:-1].split("\n")

for word in line:
    subprocess.run(word.split(" "))
