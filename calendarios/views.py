from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from calendarios.models import Calendario, Periodo, Tiempo
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from planificador.views import UserInfoMixin
from calendarios.forms import CalendarioForm


class CalendarioListView(UserInfoMixin, ListView):
    """docstring for CalendarioListView"""
    context_object_name = "calendarios"
    template_name = "calendarios/calendario_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(CalendarioListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Calendario.objects.filter(organizacion=self.request.user.get_profile().organizacion)


class CalendarioDetailView(object):
	"""docstring for CalendarioDetailView"""
	pass


class CalendarioUpdateView(object):
	"""docstring for CalendarioUpdateView"""
	pass


class CalendarioCreateView(UserInfoMixin, CreateView):
    model = Calendario
    template_name = "calendarios/calendario_create.html"
    form_class = CalendarioForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(CalendarioCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
        return super(CalendarioCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(CalendarioCreateView, self).get_context_data(**kwargs)
        return context


class CalendarioDeleteView(object):
	"""docstring for CalendarioDeleteView"""
	pass