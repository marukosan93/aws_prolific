import json
import numpy as np
import random
import csv
import sys
import subprocess

INPUT_FILE = sys.argv[1]  #CSV file to be used as input
STUDY = sys.argv[2]  #Short string identifying the study in aws
N_BATCHES = sys.argv[3] #Batch size, random shuffle works only with relatively small batches
N_REPETITION = sys.argv[4] #How many times do the batches need to be completed?
RESHUFFLE_IF_ADIACENT_SIMILAR = sys.argv[5] #Can be either 1 or 0, if 0 the batches are just randomly shuffled but closeby elements could be too similar, if 1 the reshuffling batches mechanism is implemented, but items_weights and threshold need to be set properly

#item weights need to be set, the elements are all column of the csv except for the primarykey
items_weights = [('HIT_profession',2),('HIT_healthclaim',2),('HIT_profilepic',2),('HIT_likes',1),('HIT_shares',1)]
#If the summed weights are over the threshold it means that the two scenarios are similar
threshold = 3

#Primary key for the database, uniquely identifies the scenario, don't change otherwise back end won't work
primary_key = 'HIT_scenarioID'

#finds item in list of dictionaries based on key-value
def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return int(i)
    return -1

#Computes a similarity score between two scenarios based on arbitrary weights and threshold
def compute_similarity(item1_ind,item2_ind,scen_items):
    item1 = scen_items[int(find(scen_items,primary_key,item1_ind))]
    item2 = scen_items[int(find(scen_items,primary_key,item2_ind))]
    similarity = 0
    for item_weight in items_weights:
        if (item1[item_weight[0]] == item2[item_weight[0]]):
            similarity+= item_weight[1]
    if similarity > threshold:
        return True
    else:
        return False

#Check if there are similar adiacent elements in list
def detect_similar(hits_list,scen_items):
    similar = False
    for i in range(0,len(hits_list)-1):
        if (compute_similarity(hits_list[i],hits_list[i+1],scen_items)):
            similar = True
    return similar

#Open the csv file as a list of dictionaries
with open(INPUT_FILE, "r") as f:
    reader = csv.DictReader(f)
    scen_items = list(reader)

number_batches = int(N_BATCHES)

complete_list = np.arange(1,len(scen_items)+1)
#randomly shuffles the scenarios
np.random.shuffle(complete_list)
#splits scenarios in batches
batch_scenarios = np.array_split(complete_list, number_batches)

#elements to add to DB
act = "0"
app = "0"
ava = str(N_REPETITION)
bid = 1
comp = "0"

cmd1 = "aws dynamodb batch-write-item --request-items"
cmd2 = "{\"Batches_DB_"+STUDY+"\": ["
#For each batch an entry is added to the DB
for count, batch in enumerate(batch_scenarios):
    hits_list = list(map(str, batch.tolist()))
    simile = True
    if RESHUFFLE_IF_ADIACENT_SIMILAR == 1:
        while (simile):
            random.shuffle(hits_list)
            simile = detect_similar(hits_list,scen_items)
    hits_parsed = ""
    for hit in hits_list:
        hits_parsed += "{\"S\": \""
        hits_parsed += str(hit)
        hits_parsed += "\"},"
    put_req = "{\"PutRequest\": {\"Item\":{\"Batch_ID\": {\"S\": \""+str(bid)+"\"},\"approved\": {\"S\": \""+app+"\"},\"available\": {\"S\": \""+ava+"\"},\"active\": {\"S\": \""+act+"\"},\"completed\": {\"S\": \""+comp+"\"},\"HITs\": {\"L\": ["+hits_parsed[:-1]+"]}}}},"
    cmd2 += put_req
    bid+=1

    if (count+1)%25 == 0 or count+1 == number_batches:
        cmd2 = cmd2[:-1]
        cmd2 += "]}"
        cmdlist = cmd1.split(" ")
        cmdlist.append(cmd2)
        subprocess.run(cmdlist)
        cmd2 = "{\"Batches_DB_"+STUDY+"\": ["
