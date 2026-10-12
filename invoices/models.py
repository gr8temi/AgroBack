from django.db import models

from core.models import User, Farm


def generate_invoice_number(farm, invoice_date):
    date_str = invoice_date.strftime('%y%m%d')
    prefix = f"INV-{date_str}-"

    last_invoice = (
        Invoice.objects
        .select_for_update()
        .filter(farm=farm, invoice_number__startswith=prefix)
        .order_by('-invoice_number')
        .first()
    )

    if last_invoice:
        last_counter = int(last_invoice.invoice_number.split('-')[-1])
        new_counter = last_counter + 1
    else:
        new_counter = 1

    return f"{prefix}{new_counter:03d}"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    )
    CATEGORY_CHOICES = (
        ('egg_sales', 'Egg Sales'),
        ('bird_sales', 'Bird Sales'),
        ('manure_sales', 'Manure Sales'),
        ('other', 'Other'),
    )

    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='invoices')
    related_flock = models.ForeignKey(
        'flocks.Flock', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='invoices',
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    invoice_date = models.DateField()
    due_date = models.DateField()

    customer_name = models.CharField(max_length=255)
    customer_phone = models.CharField(max_length=20, blank=True, default='')
    customer_email = models.EmailField(blank=True, default='')
    customer_address = models.TextField(blank=True, default='')

    farm_name = models.CharField(max_length=255)
    farm_phone = models.CharField(max_length=20, blank=True, default='')
    farm_email = models.EmailField(blank=True, default='')
    farm_address = models.TextField(blank=True, default='')
    payment_details = models.JSONField(default=dict, blank=True)

    notes = models.TextField(blank=True, default='')
    terms = models.TextField(blank=True, default='')

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']
        indexes = [
            models.Index(fields=['farm', 'status']),
            models.Index(fields=['farm', 'invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order']

    def __str__(self):
        return f"{self.description} (x{self.quantity})"
