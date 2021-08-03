#!/bin/sh
echo "Creating DB"
STUDYNAME=${1:?"missing argument, please add study name ( short string identifying the study in aws, for example 'credibility' )"}

aws dynamodb create-table \
    --table-name "Workers_DB_"$STUDYNAME \
    --attribute-definitions \
        AttributeName=Prolific_ID,AttributeType=S \
    --key-schema \
        AttributeName=Prolific_ID,KeyType=HASH \
--provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
        
aws dynamodb create-table \
    --table-name "Batches_DB_"$STUDYNAME \
    --attribute-definitions \
        AttributeName=Batch_ID,AttributeType=S \
    --key-schema \
        AttributeName=Batch_ID,KeyType=HASH \
--provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5
        
aws dynamodb create-table \
    --table-name "Results_DB_"$STUDYNAME \
    --attribute-definitions \
        AttributeName=UID,AttributeType=S \
    --key-schema \
        AttributeName=UID,KeyType=HASH \
--provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5        
        
aws dynamodb create-table \
    --table-name "Scenarios_DB_"$STUDYNAME \
    --attribute-definitions \
        AttributeName=HIT_scenarioID,AttributeType=S \
    --key-schema \
        AttributeName=HIT_scenarioID,KeyType=HASH \
--provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5        
        
