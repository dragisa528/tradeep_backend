from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render

from graphene_django.views import GraphQLView

# from django.views.generic.base import RedirectView

# favicon_view = RedirectView.as_view(url='/favicon.ico', permanent=True)

# def render_react(request):
#     return render(request, "index.html")

urlpatterns = [
    # ...
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # re_path(r'^favicon\.ico$', favicon_view),
    # re_path(r"^(?:.*)/?$", render_react),
    # re_path(r"^(?!static)(?:.*)/?$", render_react),
]
