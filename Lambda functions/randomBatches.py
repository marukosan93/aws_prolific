import json
import numpy as np
import boto3
from boto3.dynamodb.conditions import Key
from operator import itemgetter
import random 

# create a DynamoDB object using the AWS SDK
dynamodb = boto3.resource('dynamodb')
# use the DynamoDB object to select our table
table_batches = dynamodb.Table('Batches_DB')
table_scenarios = dynamodb.Table('Scenarios_DB')


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return int(i)
    return -1
    
def compute_similarity(item1_ind,item2_ind,scen_items):
    
    item1 = scen_items[int(find(scen_items,'HIT_scenarioID',item1_ind))]
    item2 = scen_items[int(find(scen_items,'HIT_scenarioID',item2_ind))]
    similarity = 0
    if (item1['HIT_profession'] == item2['HIT_profession']):
        similarity+=2
    if (item1['HIT_healthclaim'] == item2['HIT_healthclaim']):
        similarity+=2
    if (item1['HIT_profilepic'] == item2['HIT_profilepic']):
        similarity+=2
    if (item1['HIT_likes'] == item2['HIT_likes']):
        similarity+=1
    if (item1['HIT_shares'] == item2['HIT_shares']):
        similarity+=1     
    if similarity > 3:
        return True
    else:
        return False

def detect_similar(hits_list,scen_items):
    similar = False
    for i in range(0,len(hits_list)-1):
        if (compute_similarity(hits_list[i],hits_list[i+1],scen_items)):
            similar = True
    return similar

def lambda_handler(event, context):
    # TODO implement
    
    number_of_batches = 72 #Shuffling only works for small batch sizes
    
    complete_list = np.arange(1,649)
    np.random.shuffle(complete_list)
    
    batch_scenarios = np.array_split(complete_list, number_of_batches)

    act = "0"
    app = "0"
    ava = "5"
    bid = 1
    comp = "0"
    
    
    response_scan = table_scenarios.scan(**{})
    scen_items = response_scan['Items']
        
    for batch in batch_scenarios:
        hits_list = list(map(str, batch.tolist()))
        simile = True
        
     
    
        while (simile):
            random.shuffle(hits_list)
            simile = detect_similar(hits_list,scen_items)
            

    # write to the DynamoDB table using the object we instantiated and save response in a variable
        table_batches.put_item(
            Item={
                  "active": act,
                  "approved": app,
                  "available": ava,
                  "Batch_ID": str(bid),
                  "completed": comp,
                  "HITs": hits_list})
        bid+=1
# return a properly formatted JSON object
    return {
        'statusCode': 200,
        'body': 'done'
    }
