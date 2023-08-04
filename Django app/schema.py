import graphene
from graphene_django import DjangoObjectType
from training_api.models import Task

class YourModelType(DjangoObjectType):
    class Meta:
        model = Task

class Query(graphene.ObjectType):
    all_yourmodels = graphene.List(Task)

    def resolve_all_yourmodels(self, info):
        return Task.objects.all()

schema = graphene.Schema(query=Query)