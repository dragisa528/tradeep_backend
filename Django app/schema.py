import graphene
from graphene_django import DjangoObjectType
from .models import YourModel

class YourModelType(DjangoObjectType):
    class Meta:
        model = YourModel

class Query(graphene.ObjectType):
    all_yourmodels = graphene.List(YourModelType)

    def resolve_all_yourmodels(self, info):
        return YourModel.objects.all()

schema = graphene.Schema(query=Query)