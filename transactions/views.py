from django.shortcuts import render,get_object_or_404,redirect
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Transaction,Transfer
from .forms import DepositForm,WithdrawForm,LoanRequestForm,TransferForm
from .constants import DEPOSIT, WITHDRAWAL,LOAN, LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.views import View
from accounts.models import UserBankAccount
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage,EmailMultiAlternatives
from django.template.loader import render_to_string
# Create your views here.

def send_transaction_email(user, amount ,subject, template):
    message = render_to_string(template,{
        'user': user,
        'amount': amount
    })
    send_email = EmailMultiAlternatives(subject, '', to=[user.email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()


# ei view k inherit kore withdraw , loan and deposit korbo
class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                'account' : self.request.user.account,
            }
        )
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title':self.title
        })
        return context

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial  = {'transaction_type': DEPOSIT}
        return initial 
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        account.save(
            update_fields = ['balance']
        )
        send_transaction_email(self.request.user, amount, 'Deposit Message', 'transactions/deposit_mail.html')
        messages.success(self.request, f'{amount}$ was deposit successfully')
        return super().form_valid(form)
    
class WithdrawalMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdrawal'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(
            update_fields = ['balance']
        )
        messages.success(self.request, f'{amount}$ was withdrawal successfully')
        send_transaction_email(self.request.user, amount, 'Withdrawal Message', 'transactions/withdrawal_email.html')
        return super().form_valid(form)
    



    
class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_laon_count = Transaction.objects.filter(account = self.request.user.account, transaction_type = LOAN, load_aaprove = True).count()
        if current_laon_count >= 3:
            return HttpResponse('You have cross your limit')
        messages.success(self.request, f'{amount}$ loan request successfully Sent to admin')
        send_transaction_email(self.request.user, amount, 'Loan Request Message', 'transactions/loan_email.html')
        return super().form_valid(form)
    

class TransactionReportView(LoginRequiredMixin,ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0
    context_object_name = 'report_list'

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account = self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str,'%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str,'%Y-%m-%d').date()

            queryset = queryset.filter(timestamp__date__gte = start_date_str, timestamp__date__lte = end_date_str)

            self.balance = Transaction.objects.filter(timestamp__date__gte = start_date, timestamp__date__lte = end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account':self.request.user.account
        })
        return context
    

class PayLoanView(LoginRequiredMixin,View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id= loan_id)
        
        if loan.load_aaprove: # user loan pay korte parbe jokhon loan approve hobe
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.account
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(self.request, f'You amount is grater than account balance')
                return redirect('loan_list')
        
class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(account = user_account,transaction_type = LOAN)
        return queryset
    

@login_required
def transfer(request):
    if request.method == 'POST':
        form = TransferForm(request.POST)
        if form.is_valid():
            receiver_account_no = form.cleaned_data['receiver_account_no'].account_no
            amount = form.cleaned_data['amount']
            try:
                sender_account_no = UserBankAccount.objects.get(user=request.user)  
                receiver_account_no = UserBankAccount.objects.get(account_no=receiver_account_no)
                if sender_account_no.balance >= amount:
                    sender_account_no.balance -= amount
                    receiver_account_no.balance += amount
                    sender_account_no.save()
                    receiver_account_no.save()
                    Transfer.objects.create(sender_account_no=sender_account_no, receiver_account_no=receiver_account_no, amount=amount)
                    messages.success(request, f"Successfully transferred ${amount} to {receiver_account_no}.")
                else:
                    messages.error(request, "Insufficient balance.")
            except UserBankAccount.DoesNotExist:
                messages.error(request, f"Account with account number {receiver_account_no} not found.")
            return redirect('transfer')
    else:
        form = TransferForm()
    return render(request, 'transactions/transfer_money.html', {'form': form})



