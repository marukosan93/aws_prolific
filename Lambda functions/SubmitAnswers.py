# import the json utility package since we will be working with a JSON object
import json
# import the AWS SDK (for Python the package name is boto3)
import boto3
from boto3.dynamodb.conditions import Key
from operator import itemgetter

def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return int(i)
    return -1

def get_code(studyname,table_completion):
    try:
        response = table_completion.get_item(Key={'studyname' : studyname})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']['completion_code']

def get_batch(batch_ID,table_batches):
    try:
        response = table_batches.get_item(Key={'Batch_ID' : batch_ID})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

def get_worker(prolific_ID,table_workers):
    try:
        response = table_workers.get_item(Key={'Prolific_ID' : prolific_ID})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

def string_to_list(stringans):
    anslist=stringans
    anslist = anslist.replace('(','')
    anslist = anslist.replace(')','')
    anslist = anslist.replace('[','')
    anslist = anslist.replace(']','')
    anslist = anslist.split(",")
    anslist = list(zip(anslist[::3], anslist[1::3], anslist[2::3])) 
    return anslist
    
# define the handler function that the Lambda service will use as an entry point
def lambda_handler(event, context):
# extract values from the event object we got from the Lambda service and store in a variable
    pId = event['prolificId']
    ans_list = json.loads(event['answers'])
    
    dynamodb = boto3.resource('dynamodb')
    #takes the studyname from API call, so it knows to access the DB for the specific study
    studyname = event['studyname']
    table_workers = dynamodb.Table('Workers_DB_'+studyname)
    table_batches = dynamodb.Table('Batches_DB_'+studyname)
    table_scenarios = dynamodb.Table('Scenarios_DB_'+studyname)
    table_results = dynamodb.Table('Results_DB_'+studyname)
    table_completion = dynamodb.Table('Completion_codes')

    completion_code = get_code(studyname,table_completion)
    
    #looks for the batch that was assigned to that worker
    worker_DB_item = get_worker(pId,table_workers)
    batch_ID = worker_DB_item['Batch_ID']
    #looks for the HITs list associated to that batch
    batch_DB_item = get_batch(batch_ID,table_batches)
    active_counter = batch_DB_item['active']
    completed_counter = batch_DB_item['completed']

    active_counter = str(int(active_counter)-1)
    completed_counter = str(int(completed_counter)+1)

    table_workers.update_item(
        Key={'Prolific_ID': pId},
        UpdateExpression="SET Answers = :ans, St = :stat",
        ExpressionAttributeValues={":ans": ans_list, ":stat":"completed"}
    )
    
    table_batches.update_item(
        Key={'Batch_ID': batch_ID},
        UpdateExpression="SET active = :act, completed = :cmp",
        ExpressionAttributeValues={":act": active_counter, ":cmp":completed_counter}
    )
    
    response_scan = table_scenarios.scan(**{})
    scen_items = response_scan['Items']
    
    for answer in ans_list:
        scenario_ID_item = scen_items[find(scen_items,'HIT_scenarioID',str(answer['HIT_scenarioID']))]
        
        #Create a dictionary contatining the answers, time and IDs
        Item={
            'UID': str(answer['HIT_scenarioID'])+"_"+pId,
            'Prolific_ID': pId,
            'Study_ID':worker_DB_item['Study_ID'],
            'Session_ID':worker_DB_item['Session_ID'],
            'Time[ms]':str(answer['Time'])
        }
        #Add answer fields
        for key_ans in answer:
            if key_ans != 'HIT_scenarioID' and key_ans != 'Time':
                Item[key_ans] = answer[key_ans]
        
        #Add scenario specific fields
        list_of_scenario_keys = list(scenario_ID_item.keys())
        for scen_key in list_of_scenario_keys:
            Item[scen_key] = scenario_ID_item[scen_key]
        
        
            
        #In the credibility study two extra fields are parsed from the profile pic
        if studyname == "credibility": 
            pic = scenario_ID_item['HIT_profilepic']
            pic = pic.split("-")
            race = pic[1][0]
            gender = pic[1][1]
            if race == 'A':
                race = "Asian"       
            if race == 'B':
                race = "Black"        
            if race == 'W':
                race = "White"        
            if gender == 'M':
                gender = "Male"
            if gender == 'F':
                gender = "Female"
            Item['HIT_race'] = race
            Item['HIT_gender'] = gender

        #Add to table
        table_results.put_item(Item=Item)

# return a properly formatted JSON object
    return {
        'statusCode': 200,
        #'body': json.dumps(ans_list)
        'body': json.dumps(completion_code)
    }
