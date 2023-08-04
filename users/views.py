from django.shortcuts import render, redirect
from users.forms import UserForm
from users.models import UserModel
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
import json
from rest_framework import serializers
from . import models
from rest_framework.decorators import api_view
from django.views.decorators.csrf import ensure_csrf_cookie
import json


class MenuSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserModel
        fields = "__all__"


@ensure_csrf_cookie
@api_view(["POST"])
def register(request):
    userload = []
    if request.method == "POST":
        print(request.body)
        temp = json.loads(request.body)
        if temp["password1"] == temp["password2"]:
            data = {
                "upass": temp["password1"],
                "username": temp["username"],
                "uid": "111",
                "email": temp["email"],
            }
            tt = json.dumps(data)
            form = UserForm(data)  # json handling for POST
            if form.is_valid():
                try:
                    form.save()
                    return HttpResponse("OK")
                except Exception as e:
                    print(e)
                    pass
            else:
                return HttpResponse("Form inValid")
    else:
        form = UserForm()
    return form


@ensure_csrf_cookie
@api_view(["POST"])
def login(request):
    if request.method == "POST":
        print(request.body)
        return 1

@ensure_csrf_cookie
@api_view(["GET"])
def show(request):
    employees = UserModel.objects.all()
    serializer = MenuSerializer(employees, many=True)
    return Response(data=serializer.data, status=status.HTTP_200_OK)


@api_view(["UPDATE"])
def edit(request, id):
    employee = UserModel.objects.get(uid=id)
    return Response(status=status.HTTP_200_OK)


@api_view(["UPDATE"])
def update(request, id):
    employee = UserModel.objects.get(uid=id)
    form = UserForm(request.POST, instance=employee)
    if form.is_valid():
        form.save()
        return redirect("/show")
    return Response(status=status.HTTP_200_OK)


@api_view(["DELETE"])
def destroy(request, id):
    employee = UserModel.objects.get(uid=id)
    employee.delete()
    return Response(status=status.HTTP_200_OK)
