import json
import random
import csv
import sys
import subprocess
from math import ceil

INPUT_FILE = sys.argv[1]  #CSV file to be used as input
STUDY = sys.argv[2]  #Short string identifying the study in aws
N_BATCHES = sys.argv[3] #Batch size, random shuffle works only with relatively small batches
N_REPETITION = sys.argv[4] #How many times do the batches need to be completed?
SORTING = sys.argv[5] #Can be either 1 or 0, if 0 the batches are just randomly sorted, if 1 batches are sorted uniformly (similar scenarios in batch are minimised)

#item weights need to be set, the elements are all column of the csv except for the primarykey
items_weights = [('HIT_profession',1),('HIT_healthclaim',1),('HIT_profilepic',1),('HIT_likes',1),('HIT_shares',1)]

#Primary key for the database, uniquely identifies the scenario, don't change otherwise back-end won't work
primary_key = 'HIT_scenarioID'

#Computes a similarity score between two scenarios based on weights
def compute_similarity(scenario1,scenario2):
    similarity = 0
    for item_weight in items_weights:
        if (scenario1[item_weight[0]] == scenario2[item_weight[0]]):
            similarity+= item_weight[1]
    return similarity

#Sums the total similarity scores of a batch and scenario
def calculate_similarity_score_batch_scen(scenario,batch):
    if len(batch) == 0:
        return 0
    else:
        total_similar = 0
        for count, batch_scenario in enumerate(batch):
            similarity = compute_similarity(scenario,batch_scenario)
            if count == len(batch)-1:   #add higher weight for the last element, thus disencouraging subsequent elements from being too similar
                similarity = 2*similarity
            total_similar += similarity
        return total_similar

#Open the csv file as a list of dictionaries
with open(INPUT_FILE, "r") as f:
    reader = csv.DictReader(f)
    scenarios = list(reader)

number_batches = int(N_BATCHES)
#randomly shuffles scenarios
random.shuffle(scenarios)
#makes sure batches are evenly sized
max_batch_size = ceil(len(scenarios)/number_batches)
#Splits scenarios in equal sized buckets (doesn't care about similarity)
if int(SORTING) == 0:
    #splits scenarios in batches
    batches = [[] for x in range(number_batches)]
    #distributes the scenarios in N_BATCHES evenly sized batches
    for scenario in scenarios:
        for batch in batches:
            if len(batch) < max_batch_size:
                batch.append(scenario)
                score = calculate_similarity_score_batch_scen(scenario,batch)
                break

#Splits scenarios in equal sized buckets with minimised similarity
else:
    if int(SORTING) == 1:
        #Creates empty batches
        batches = [[] for x in range(number_batches)]
        for scenario in scenarios:
            min_batch_score = sys.maxsize
            candidate = None
            for batch in batches:
                if len(batch) < max_batch_size:
                    score = calculate_similarity_score_batch_scen(scenario,batch)
                    if score < min_batch_score:
                        min_batch_score = score
                        candidate = batch
            candidate.append(scenario)
    else:
        print("SORTING agrument can be eiher 1 or 0")

#elements to add to DB
act = "0"
app = "0"
ava = str(N_REPETITION)
bid = 1
comp = "0"

cmd1 = "aws dynamodb batch-write-item --request-items"
cmd2 = "{\"Batches_DB_"+STUDY+"\": ["
#For each batch an entry is added to the DB
for count, batch in enumerate(batches):
    if SORTING == 0:
        batch = list(map(str, batch.tolist()))
    hits_parsed = ""
    for scen in batch:
        hits_parsed += "{\"S\": \""
        hit = scen['HIT_scenarioID']
        hits_parsed += hit
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
