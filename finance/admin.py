from django.contrib import admin
from .models import Transaction, ChartAccount, BankAccountEntries, BankAccount

admin.site.register(ChartAccount)
admin.site.register(BankAccountEntries)
admin.site.register(Transaction)
admin.site.register(BankAccount)
