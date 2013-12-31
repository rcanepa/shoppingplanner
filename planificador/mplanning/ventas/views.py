# Create your views here.
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import user_passes_test
from planificador.views import UserInfoMixin
from ventas.models import Controlventa
from ventas.forms import ControlventaForm


class ControlventaListView(UserInfoMixin, ListView):
    """docstring for ControlventaListView"""
    context_object_name = "registros"
    template_name = "ventas/controlventa_list.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ControlventaListView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        """Override get_querset so we can filter on request.user """
        return Controlventa.objects.filter(organizacion=self.request.user.get_profile().organizacion)


class ControlventaDetailView(UserInfoMixin, DetailView):
	"""docstring for CalendarioDetailView"""
	model = Controlventa
	template_name = "ventas/controlventa_detail.html"
	
	@method_decorator(login_required)
	def dispatch(self, *args, **kwargs):
		return super(ControlventaDetailView, self).dispatch(*args, **kwargs)
	def get_context_data(self, **kwargs):
		context = super(ControlventaDetailView, self).get_context_data(**kwargs)
		return context


class ControlventaUpdateView(UserInfoMixin, UpdateView):
	"""docstring for ControlventaUpdateView"""
	model = Controlventa
	template_name = "ventas/controlventa_update.html"
	form_class = ControlventaForm
	@method_decorator(login_required)
	@method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
	def dispatch(self, *args, **kwargs):
		return super(ControlventaUpdateView, self).dispatch(*args, **kwargs)
	def get_context_data(self, **kwargs):
		context = super(ControlventaUpdateView, self).get_context_data(**kwargs)
		return context


class ControlventaCreateView(UserInfoMixin, CreateView):
    model = Controlventa
    template_name = "ventas/controlventa_create.html"
    form_class = ControlventaForm

    @method_decorator(login_required)
    @method_decorator(user_passes_test(lambda u: u.groups.filter(name="Administrador")))
    def dispatch(self, *args, **kwargs):
        return super(ControlventaCreateView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.organizacion = self.request.user.get_profile().organizacion
        return super(ControlventaCreateView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(ControlventaCreateView, self).get_context_data(**kwargs)
        return context