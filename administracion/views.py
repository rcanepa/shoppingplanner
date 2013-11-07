from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm


@login_required()
def index(request):
    return render_to_response('administracion/index.html', 
                              {'full_name': request.user.first_name + " " + request.user.last_name,
                               'admin': request.user.groups.filter(name="Administrador")})