import json
from django import forms
from graphene_django import DjangoObjectType, DjangoListField, DjangoMutation
import graphene

from training_api.models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'

class TaskType(DjangoObjectType):
    class Meta:
        model = Task

class CreateTaskMutation(DjangoMutation):
    class Arguments:
        json_data = graphene.String(required=True)

    task = graphene.Field(TaskType)

    @classmethod
    def mutate(cls, root, info, json_data):
        try:
            data = json.loads(json_data)
            form = TaskForm(data)
            if form.is_valid():
                task = form.save()
                return CreateTaskMutation(task=task)
            else:
                return CreateTaskMutation(errors=form.errors)
        except json.JSONDecodeError:
            return CreateTaskMutation(errors={'json_data': 'Invalid JSON format'})

class Mutation(graphene.ObjectType):
    create_task = CreateTaskMutation.Field()



schema = graphene.Schema(query=Query, mutation=Mutation)