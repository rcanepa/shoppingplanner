from django.contrib.staticfiles.templatetags.staticfiles import static
from django.views.generic import TemplateView
from braces.views import GroupRequiredMixin
from braces.views import LoginRequiredMixin
from planificador.views import UserInfoMixin


class AdminView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, TemplateView):
    """Vista pagina de inicio Administradores"""
    template_name = 'administracion/index.html'
    group_required = u'Administrador'


#class AdminAngularView(GroupRequiredMixin, LoginRequiredMixin, UserInfoMixin, TemplateView):
class AdminAngularView(UserInfoMixin, TemplateView):
    """Vista pagina de inicio Administradores"""
    #template_name = 'administracion/index.html'
    template_name = static('frontend/admin/index.html')
    #group_required = u'Administrador'
