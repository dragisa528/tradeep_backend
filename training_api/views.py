from django.shortcuts import render
import boto3
import graphene
from graphene_django import DjangoObjectType
from models import Task  # Assuming you have a Task model

class TrainMutation(graphene.Mutation):
    class Arguments:
        # Define the arguments for the mutation (e.g., JSON data)
        json_data = graphene.String(required=True)


def mutate(self, info, json_data):

    sqs = boto3.client('sqs', region_name='your_region')
    queue_url = 'your_queue_url'
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json_data
    )

    return TrainMutation(success=True, message="Task created successfully")