from django.shortcuts import render, redirect
from django.views.generic import FormView,CreateView
from .forms import UserRegistrationForm,UserUpdateForm
from django.contrib.auth import login,logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView,LogoutView
from django.views import View
from django.contrib import messages
# Create your views here.
class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('register')

    def form_valid(self, form):
        user = form.save()
        login(self.request,user)
        print(user)
        return super().form_valid(form) # form_valid fc call hobe jdi sob thik thake
    
    ######################## conceptual ##########################
class UserRegistrationView1(CreateView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('register')

    def form_valid(self, form):
        login(self.request,self.get_object)
        return super().form_valid(form) 

    #############################################################
class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_valid(self, form):
        messages.success(self.request, 'Login successfully. Welcome Back !')
        return super().form_valid(form)
    
# class UserLogoutView(LogoutView):
#     def get(self):
#         if self.request.user.is_authenticated:
#             logout(self.request)
#         return reverse_lazy('home')
    

def UserLogout(request):
    logout(request)
    messages.info(request, 'Logout successfully.!')
    return redirect('home')

class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance = request.user)
        return render(request, self.template_name, {'form':form})
    
    def post(self, request):
        form  = UserUpdateForm(request.POST, instance =  request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
        return render(request, self.template_name, {'form':form})