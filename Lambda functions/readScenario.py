# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
#import exceptions library
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import numpy as np

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return int(i)
    return -1


def get_worker(prolific_ID,table_workers):
    try:
        response = table_workers.get_item(Key={'Prolific_ID' : prolific_ID})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']
        
def get_batch(batch_ID,table_batches):
    try:
        response = table_batches.get_item(Key={'Batch_ID' : batch_ID})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
    #takes the prolific_ID from the Api call ( which was extracted from the url)
    prolific_ID = event['prolificId']
    
    #takes the studyname from API call, so it knows to access the DB for the specific study
    studyname = event['studyname']
    dynamodb = boto3.resource('dynamodb')
    # return a properly formatted JSON object

    table_scenarios = dynamodb.Table('Scenarios_DB_'+studyname)
    table_workers = dynamodb.Table('Workers_DB_'+studyname)
    table_batches = dynamodb.Table('Batches_DB_'+studyname)

    #looks for the batch that was assigned to that worker
    worker_DB_item = get_worker(prolific_ID,table_workers)
    batch_ID = worker_DB_item['Batch_ID']
    #looks for the HITs list associated to that batch
    batch_DB_item = get_batch(batch_ID,table_batches)
    scenario_ID_list = batch_DB_item['HITs']

    response_scan = table_scenarios.scan(**{})
    scen_items = response_scan['Items']
    
    result = "{"
    result += "\"scenarios\":["
    for scen in scenario_ID_list:
        scenario_index = find(scen_items,'HIT_scenarioID',scen)
        item = scen_items[scenario_index]
        result += json.dumps(item)
        result += ","
    result = result[:-1]
    result += "]}"
    
# return a properly formatted JSON object
    return {
        'statusCode': 200,
        'body': result
    }
