from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
# from django.shortcuts import render

from graphene_django.views import GraphQLView
from django.contrib import admin
from django.urls import path, include, re_path
from django.contrib.auth import views as auth_views

# from django.views.generic.base import RedirectView
# favicon_view = RedirectView.as_view(url='/favicon.ico', permanent=True)
# def render_react(request):
#     return render(request, "index.html")

urlpatterns = [
    # ...
    path("graphql/", csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('admin/', admin.site.urls),
    path('aimodel', include('aimodel.urls')),
    path('users', include('users.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # re_path(r'^favicon\.ico$', favicon_view),
    # re_path(r"^(?:.*)/?$", render_react),
    # re_path(r"^(?!static)(?:.*)/?$", render_react),
]