from decimal import Decimal

from rest_framework import serializers

from .models import Invoice, InvoiceLineItem, generate_invoice_number


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = ('id', 'description', 'quantity', 'unit_price', 'total', 'sort_order')
        read_only_fields = ('id', 'total')


class InvoiceSerializer(serializers.ModelSerializer):
    line_items = InvoiceLineItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = (
            'invoice_number', 'farm', 'created_by',
            'farm_name', 'farm_phone', 'farm_email', 'farm_address',
            'payment_details', 'subtotal', 'grand_total',
            'created_at', 'updated_at',
        )

    def validate_related_flock(self, value):
        if value is None:
            return value
        request = self.context.get('request')
        if request and value.farm_id != request.user.farm_id:
            raise serializers.ValidationError("Flock does not belong to your farm.")
        return value

    def validate_line_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one line item is required.")
        return value

    def validate(self, attrs):
        if self.instance and self.instance.status in ('paid', 'cancelled'):
            raise serializers.ValidationError("Cannot modify a paid or cancelled invoice.")
        return attrs

    def _compute_totals(self, line_items_data):
        subtotal = Decimal('0')
        for item in line_items_data:
            item['total'] = item['quantity'] * item['unit_price']
            subtotal += item['total']
        return subtotal

    def create(self, validated_data):
        line_items_data = validated_data.pop('line_items')
        request = self.context['request']
        farm = request.user.farm

        subtotal = self._compute_totals(line_items_data)

        validated_data['farm'] = farm
        validated_data['created_by'] = request.user
        validated_data['invoice_number'] = generate_invoice_number(farm, validated_data['invoice_date'])

        validated_data['farm_name'] = farm.name
        validated_data['farm_phone'] = farm.phone
        validated_data['farm_email'] = farm.email
        validated_data['farm_address'] = farm.address
        validated_data['payment_details'] = farm.payment_details

        validated_data['subtotal'] = subtotal
        validated_data['grand_total'] = subtotal

        invoice = Invoice.objects.create(**validated_data)

        for idx, item_data in enumerate(line_items_data):
            item_data.setdefault('sort_order', idx)
            InvoiceLineItem.objects.create(invoice=invoice, **item_data)

        return invoice

    def update(self, instance, validated_data):
        line_items_data = validated_data.pop('line_items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if line_items_data is not None:
            subtotal = self._compute_totals(line_items_data)
            instance.subtotal = subtotal
            instance.grand_total = subtotal

            instance.line_items.all().delete()
            for idx, item_data in enumerate(line_items_data):
                item_data.setdefault('sort_order', idx)
                InvoiceLineItem.objects.create(invoice=instance, **item_data)

        instance.save()
        return instance
