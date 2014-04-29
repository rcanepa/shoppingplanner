
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.text import slugify
from django.views.generic import View, TemplateView, ListView, DetailView
from userprofile.forms import RegistrationForm
from userprofile.models import UserProfile
from braces.views import LoginRequiredMixin
import csv
import json


# Mixins
class UserInfoMixin(object):
    """Obtiene informacion general del usuario visitante"""
    def get_context_data(self, *args, **kwargs):
        context = super(UserInfoMixin, self).get_context_data(*args, **kwargs)
        context['full_name'] = self.request.user.first_name + " " + self.request.user.last_name
        #Revisa si el usuario pertenece al grupo Administrador, devuelve True o False
        context['admin'] = bool(self.request.user.groups.filter(name="Administrador"))
        return context


def login(request):
	c = {}
	c.update(csrf(request))
	return render_to_response('login.html', c)


def auth_view(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(username=username, password=password)
    
    if user is not None:
        auth.login(request, user)
        return HttpResponseRedirect('/accounts/loggedin')
    else:
        return HttpResponseRedirect('/accounts/invalid')


class LoggedInView(LoginRequiredMixin, UserInfoMixin, TemplateView):
    """Vista para usuarios que ingresan al sistema. Los lleva al home."""
    template_name = "loggedin.html"


class InvalidLogin(TemplateView):
    """Vista para ingresos invalidos."""
    template_name = 'invalid_login.html'
        

@login_required()
def logout(request):
    auth.logout(request)
    return render_to_response('logout.html')


class RegisterUserView(LoginRequiredMixin, UserInfoMixin, View):
    """Vista para el registro de nuevos usuarios"""
    form_class = RegistrationForm
    template_name = 'register.html'

    def get(self, request, *args, **kwargs):
        ''' user is not submitting the form, show them a blank registration form '''
        form = RegistrationForm()
        context = {'form': form}
        return render_to_response('register.html', context, context_instance=RequestContext(request))
        #return HttpResponseRedirect(reverse('administracion:index'))

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(username=form.cleaned_data['username'], 
                email = form.cleaned_data['email'], 
                password = form.cleaned_data['password'], 
                first_name = form.cleaned_data['first_name'], 
                last_name = form.cleaned_data['last_name'])
            user.save()
            userprofile = UserProfile(user=user, organizacion=request.user.get_profile().organizacion)
            userprofile.save()
            return HttpResponseRedirect('/accounts/register_success/')
        else:
            return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))


class RegisterSuccessView(LoginRequiredMixin, UserInfoMixin, TemplateView):
    """Vista utilizada """
    template_name = "register_success.html"


class UserListView(LoginRequiredMixin, UserInfoMixin, ListView):
    """Lista los usuarios de la organizacion"""
    model = User
    template_name = "user_list.html"

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['users'] = User.objects.filter(userprofile__organizacion=self.request.user.get_profile().organizacion)
        return context


class UserDetailView(LoginRequiredMixin, UserInfoMixin, DetailView):
    """Vista para la ficha de un usuario"""
    model = User
    template_name = "user_detail.html"
    context_object_name = "usuario"