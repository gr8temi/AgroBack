from django.contrib import admin

from .models import Invoice, InvoiceLineItem


class InvoiceLineItemInline(admin.TabularInline):
    model = InvoiceLineItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'farm', 'customer_name', 'status', 'grand_total', 'invoice_date')
    list_filter = ('status', 'farm')
    search_fields = ('invoice_number', 'customer_name')
    readonly_fields = ('invoice_number', 'created_at', 'updated_at')
    inlines = [InvoiceLineItemInline]
