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


schema = graphene.Schema(query=Query, mutation=Mutation)