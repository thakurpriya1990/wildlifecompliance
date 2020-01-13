from django.http import Http404, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.views.generic.base import View, TemplateView
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin

from datetime import datetime, timedelta

from wildlifecompliance.helpers import is_internal, prefer_compliance_management, is_model_backend, in_dbca_domain, \
    is_compliance_internal_user, is_wildlifecompliance_admin
from wildlifecompliance.forms import *
from wildlifecompliance.components.applications.models import Application
from wildlifecompliance.components.call_email.models import CallEmail
from wildlifecompliance.components.returns.models import Return
from wildlifecompliance.components.main import utils
from wildlifecompliance.exceptions import BindApplicationException
from django.core.management import call_command


class ApplicationView(DetailView):
    model = Application
    template_name = 'wildlifecompliance/dash/index.html'


class CallEmailView(DetailView):
    model = CallEmail
    template_name = 'wildlifecompliance/dash/index.html'


class ExternalApplicationView(DetailView):
    model = Application
    template_name = 'wildlifecompliance/dash/index.html'


class ExternalReturnView(DetailView):
    model = Return
    template_name = 'wildlifecompliance/dash/index.html'


class InternalView(UserPassesTestMixin, TemplateView):
    template_name = 'wildlifecompliance/dash/index.html'

    def test_func(self):
        return is_internal(self.request)

    def get_context_data(self, **kwargs):
        context = super(InternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        context['app_build_url'] = settings.DEV_APP_BUILD_URL
        return context


class ExternalView(LoginRequiredMixin, TemplateView):
    template_name = 'wildlifecompliance/dash/index.html'

    def get_context_data(self, **kwargs):
        context = super(ExternalView, self).get_context_data(**kwargs)
        context['dev'] = settings.DEV_STATIC
        context['dev_url'] = settings.DEV_STATIC_URL
        context['app_build_url'] = settings.DEV_APP_BUILD_URL
        return context


class WildlifeComplianceRoutingView(TemplateView):
    template_name = 'wildlifecompliance/index.html'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated():
            print('email: {}'.format(self.request.user.email))
            print("is_authenticated: True")
            print('is_superuser: {}'.format(self.request.user.is_superuser))
            print('is_model_backend: {}'.format(is_model_backend(self.request)))
            print('is_dbca_domain: {}'.format(in_dbca_domain(self.request)))
            print('is_compliance_internal_user: {}'.format(is_compliance_internal_user(self.request)))
            print('is_wildlifecompliance_admin: {}'.format(is_wildlifecompliance_admin(self.request)))
            print('prefer compliance management: {}'.format(prefer_compliance_management(self.request)))
            if is_internal(self.request) and prefer_compliance_management(self.request):
                return redirect('internal/call_email/')
            elif is_internal(self.request):
                return redirect('internal')
            return redirect('external')
        kwargs['form'] = LoginForm
        return super(WildlifeComplianceRoutingView, self).get(*args, **kwargs)


@login_required(login_url='wc_home')
def first_time(request):
    context = {}
    if request.method == 'POST':
        form = FirstTimeForm(request.POST)
        redirect_url = form.data['redirect_url']
        if not redirect_url:
            redirect_url = '/'
        if form.is_valid():
            # set user attributes
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.dob = form.cleaned_data['dob']
            request.user.save()
            return redirect(redirect_url)
        context['form'] = form
        context['redirect_url'] = redirect_url
        return render(request, 'wildlifecompliance/user_profile.html', context)
    # GET default
    if 'next' in request.GET:
        context['redirect_url'] = request.GET['next']
    else:
        context['redirect_url'] = '/'
    context['dev'] = settings.DEV_STATIC
    context['dev_url'] = settings.DEV_STATIC_URL
    context['app_build_url'] = settings.DEV_APP_BUILD_URL
    return render(request, 'wildlifecompliance/dash/index.html', context)


class HealthCheckView(TemplateView):
    """A basic template view not requiring auth, used for service monitoring.
    """
    template_name = 'wildlifecompliance/healthcheck.html'

    def get_context_data(self, **kwargs):
        context = super(HealthCheckView, self).get_context_data(**kwargs)
        context['page_title'] = 'Wildlife Licensing application status'
        context['status'] = 'HEALTHY'
        return context


class ManagementCommandsView(LoginRequiredMixin, TemplateView):
    template_name = 'wildlifecompliance/mgt-commands.html'

    def post(self, request):
        data = {}
        command_script = request.POST.get('script', None)
        if command_script:
            print 'running {}'.format(command_script)
            call_command(command_script)
            data.update({command_script: 'true'})

        return render(request, self.template_name, data)
