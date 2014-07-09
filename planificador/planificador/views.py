# -*- coding: utf-8 -*-
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.views.generic import View, TemplateView, ListView, DetailView
from userprofile.forms import RegistrationForm
from userprofile.models import UserProfile
from braces.views import LoginRequiredMixin
from braces.views import GroupRequiredMixin
from .forms import LoginForm


# Mixins
class UserInfoMixin(object):
    """Obtiene informacion general del usuario visitante"""
    def get_context_data(self, *args, **kwargs):
        context = super(UserInfoMixin, self).get_context_data(*args, **kwargs)
        context['full_name'] = self.request.user.first_name + " " + self.request.user.last_name
        #Revisa si el usuario pertenece al grupo Administrador, devuelve True o False
        context['admin'] = bool(self.request.user.groups.filter(name="Administrador"))
        return context


class LoginView(View):
    """Vista para el ingreso y autenticacion de usuarios al sistema"""
    template_name = 'login.html'

    def get(self, request):
        # Verificar que el usuario no se encuentre logueado.
        if request.user.is_authenticated():
            if request.user.is_staff:
                return HttpResponseRedirect('/administracion/')
            else:
                return HttpResponseRedirect('/planes/plan/list/')
        # Generar la vista de login.
        return render(
            request,
            self.template_name,
            {
                'form': LoginForm,
            },
        )

    def post(self, request):
        username = ''
        password = ''

        # Se valida que los parametros hayan sido ingresados
        if request.POST['username'] and request.POST['password']:
            username = request.POST['username']
            password = request.POST['password']
        else:
            # Si no han sido ingresados, se redirige a la pagina de login
            return render(
                request,
                self.template_name,
                {
                    'form': LoginForm(request.POST),
                    'message': 'Usuario o contraseña no ingresado.'
                }
            )

        # Validar que el usuario exista
        user = auth.authenticate(username=username, password=password)

        # Si no existe se envia un mensaje
        if not user:
            return render(
                request,
                self.template_name,
                {
                    'form': LoginForm(request.POST),
                    'message': 'Combinación usuario/contraseña incorrecta.'
                }
            )

        # Se loguea y redirige a la pagina de inicio
        auth.login(request, user)
        if user.is_staff:
            return HttpResponseRedirect('/administracion/')
        else:
            return HttpResponseRedirect('/planes/plan/list/')


class LogoutView(LoginRequiredMixin, View):
    """Vista para hacer logout del usuario solicitante."""
    def get(self, request):
        auth.logout(request)
        return HttpResponseRedirect('/')


class LoggedInView(LoginRequiredMixin, UserInfoMixin, TemplateView):
    """Vista para usuarios que ingresan al sistema. Los lleva al home."""
    template_name = "loggedin.html"


class RegisterUserView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, View):
    """Vista para el registro de nuevos usuarios"""
    form_class = RegistrationForm
    template_name = 'register.html'
    group_required = u'Administrador'

    def get(self, request, *args, **kwargs):
        ''' user is not submitting the form, show them a blank registration form '''
        form = RegistrationForm()
        context = {'form': form}
        return render_to_response('register.html', context, context_instance=RequestContext(request))

    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'])
            user.save()
            userprofile = UserProfile(user=user, organizacion=request.user.get_profile().organizacion)
            userprofile.save()
            return HttpResponseRedirect('/accounts/register_success/')
        else:
            return render_to_response('register.html', {'form': form}, context_instance=RequestContext(request))


class RegisterSuccessView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, TemplateView):
    """Vista utilizada """
    group_required = u'Administrador'
    template_name = "register_success.html"


class UserListView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, ListView):
    """Lista los usuarios de la organizacion"""
    model = User
    template_name = "user_list.html"
    group_required = u'Administrador'

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['users'] = User.objects.filter(userprofile__organizacion=self.request.user.get_profile().organizacion)
        return context


class UserDetailView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, DetailView):
    """Vista para la ficha de un usuario"""
    model = User
    template_name = "user_detail.html"
    context_object_name = "usuario"
    group_required = u'Administrador'
