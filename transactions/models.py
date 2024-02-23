from django.db import models
from accounts.models import UserBankAccount
from .constants import TRANSACTION_TYPE
from django.contrib.auth.models import User
# Create your models here.

class Transaction(models.Model):
    account = models.ForeignKey(UserBankAccount, related_name = 'transactions', on_delete= models.CASCADE)
    amount = models.DecimalField(decimal_places = 2, max_digits = 12)
    balance_after_transaction = models.DecimalField(decimal_places = 2, max_digits = 12)
    transaction_type = models.IntegerField(choices = TRANSACTION_TYPE, null = True)
    timestamp = models.DateTimeField(auto_now_add = True) # kokhon transaction korche seta
    load_aaprove = models.BooleanField(default = False)

    class Meta:
        ordering = ['timestamp'] # sort kortiche by time transaction

class Transfer(models.Model):
    sender_account_no = models.ForeignKey(UserBankAccount, related_name= 'sender', on_delete=models.CASCADE)
    receiver_account_no = models.ForeignKey(UserBankAccount,related_name= 'receiver', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.account_no}-->{self.receiver.account_no} amount :{self.amount}'

    
  