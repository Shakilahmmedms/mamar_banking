from django import forms
from .models import Transaction, Transfer
from accounts.models import UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount','transaction_type']

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save()
    


class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposti_amount = 100
        amount = self.cleaned_data.get('amount')
        if amount < min_deposti_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposti_amount} $'
            )
        return amount

class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account
        min_withdraw_amount = 500
        max_withdraw_amount = 20000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} $'
            )
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} $'
            )
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} $ your account'
                'You can not withdraw more than your account balance '
            )
        return amount
    
class LoanRequestForm(TransactionForm):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount
    

class TransferForm(forms.ModelForm):
    receiver_account_no = forms.ModelChoiceField(queryset=UserBankAccount.objects.all())
    class Meta:
        model = Transfer
        fields = ['receiver_account_no', 'amount']
    
    def save(self, commit=True):
        transfer = super().save(commit=False)
        receiver_account_no = self.cleaned_data.get('receiver_account_no')
        transfer.receiver_account_no = receiver_account_no
        if commit:
            transfer.save()
        return transfer

