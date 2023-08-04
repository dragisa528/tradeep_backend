from django import forms  
from models import Task  
class UserForm(forms.ModelForm):  
    class Meta:  
        model = Task  
        fields = "__all__"  