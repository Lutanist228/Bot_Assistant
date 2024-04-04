from django.views.generic.edit import CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from accounts.forms import CustomUserCreationForm

class RegistrationForm(CreateView):
    template_name='registration/registration_form.html'
    form_class=CustomUserCreationForm
    success_url=reverse_lazy('homepage:index')

    def form_valid(self, form):
        telegram_id = self.request.POST.get('telegram_id')
        form.instance.telegram_id = 1
        form.save()
        return super().form_valid(form)
    
    

