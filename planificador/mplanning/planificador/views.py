from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.views.generic import View, TemplateView, ListView, DetailView
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from userprofile.forms import RegistrationForm
from django.contrib.auth.models import User
from userprofile.models import UserProfile
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


class JSONResponseMixin(object):
    """
    A mixin that can be used to render a JSON response.
    """
    def render_to_json_response(self, context, **response_kwargs):
        """
        Returns a JSON response, transforming 'context' to make the payload.
        """
        return HttpResponse(
            self.convert_context_to_json(context),
            content_type='application/json',
            **response_kwargs
        )

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


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


class LoggedInView(UserInfoMixin, TemplateView):
    """Vista para usuarios que ingresan al sistema. Los lleva al home."""
    template_name = "loggedin.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInView, self).dispatch(*args, **kwargs)


class InvalidLogin(TemplateView):
    """Vista para ingresos invalidos."""
    template_name = 'invalid_login.html'
        

@login_required()
def logout(request):
    auth.logout(request)
    return render_to_response('logout.html')


class RegisterUserView(UserInfoMixin, View):
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

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RegisterUserView, self).dispatch(*args, **kwargs)


class RegisterSuccessView(UserInfoMixin, TemplateView):
    """Vista utilizada """
    template_name = "register_success.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RegisterSuccessView, self).dispatch(*args, **kwargs)


class UserListView(UserInfoMixin, ListView):
    """Lista los usuarios de la organizacion"""
    model = User
    template_name = "user_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserListView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context['users'] = User.objects.filter(userprofile__organizacion=self.request.user.get_profile().organizacion)
        return context


class UserDetailView(UserInfoMixin, DetailView):
    """Vista para la ficha de un usuario"""
    model = User
    template_name = "user_detail.html"
    context_object_name = "usuario"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserDetailView, self).dispatch(*args, **kwargs)