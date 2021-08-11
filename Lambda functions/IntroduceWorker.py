# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
from boto3.dynamodb.conditions import Key
from operator import itemgetter


# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
# extract values from the event object we got from the Lambda service and store in a variable
    pId = event['prolificId']
    stdId = event['studyId']
    sesId = event['sessionId']
    studyname = event['studyname']
    
        # create a DynamoDB object using the AWS SDK
    dynamodb = boto3.resource('dynamodb')
    # use the DynamoDB object to select our table
    table_batches = dynamodb.Table('Batches_DB_'+studyname)
    table_workers = dynamodb.Table('Workers_DB_'+studyname)

    scan_kwargs = {
        'FilterExpression': Key('available').gt('0'),
        'ProjectionExpression': "Batch_ID, available, active"    }

    #Retrieves whole table (a bit inefficient but it works well for a small db)
    response_scan = table_batches.scan(**scan_kwargs)
    items = response_scan['Items']
    
    #Checks if the worker already exists
    response_query_workers = table_workers.query(KeyConditionExpression=Key('Prolific_ID').eq(pId))['Items']
    if len(response_query_workers)>0:
        return {
            'statusCode': 200,
            'body': json.dumps('existingworker')
        }
    
    if len(items)==0:
        return {
            'statusCode': 200,
            'body': json.dumps('nobatches')
        }
 
    #Convert list of dicts in list of tuples with the values
    items_list = []
    for item in items:
        items_list.append((int(item["Batch_ID"]),int(item["available"]),int(item["active"])))
    #Get batch with maximum availability and all relevant counters
    max_item = max(items_list, key=itemgetter(1))
    batch = max_item[0]
    available_current_batch = max_item[1]
    active_current_batch = max_item[2]
    #update the counters
    available_current_batch -= 1
    active_current_batch += 1
    #write counters to db
    batch = str(batch)
    active_current_batch = str(active_current_batch)
    available_current_batch = str(available_current_batch)

    table_batches.update_item(
        Key={'Batch_ID': batch},
        UpdateExpression="SET active = :act, available = :avl",
        ExpressionAttributeValues={":act": active_current_batch,":avl":available_current_batch},
    )
    
    
# write to the DynamoDB table using the object we instantiated and save response in a variable
    table_workers.put_item(
        Item={
            'Prolific_ID': pId,
            'Study_ID':stdId,
            'Session_ID':sesId,
            'St':'active',
            'Batch_ID':batch
            })
            
    return {
        'statusCode': 200,
        'body': json.dumps('true')
    }
