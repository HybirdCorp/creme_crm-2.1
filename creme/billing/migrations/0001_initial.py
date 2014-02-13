# -*- coding: utf-8 -*-

from south.db import db
from south.v2 import SchemaMigration

from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ("creme_core", "0001_initial"),
    )
    needed_by = (
        ('creme_core', '0014_v1_4__add_vat'),
    )

    def forwards(self, orm):
        # Adding model 'SettlementTerms'
        db.create_table('billing_settlementterms', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('billing', ['SettlementTerms'])

        # Adding model 'InvoiceStatus'
        db.create_table('billing_invoicestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('billing', ['InvoiceStatus'])

        # Adding model 'QuoteStatus'
        db.create_table('billing_quotestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('billing', ['QuoteStatus'])

        # Adding model 'SalesOrderStatus'
        db.create_table('billing_salesorderstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('billing', ['SalesOrderStatus'])

        # Adding model 'CreditNoteStatus'
        db.create_table('billing_creditnotestatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
        ))
        db.send_create_signal('billing', ['CreditNoteStatus'])

        # Adding model 'AdditionalInformation'
        db.create_table('billing_additionalinformation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('billing', ['AdditionalInformation'])

        # Adding model 'PaymentTerms'
        db.create_table('billing_paymentterms', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('billing', ['PaymentTerms'])

        # Adding model 'PaymentInformation'
        db.create_table('billing_paymentinformation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bank_code', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('counter_code', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('account_number', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('rib_key', self.gf('django.db.models.fields.CharField')(max_length=12, null=True, blank=True)),
            ('banking_domiciliation', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('iban', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('bic', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(related_name='PaymentInformationOrganisation_set', to=orm['persons.Organisation'])),
        ))
        db.send_create_signal('billing', ['PaymentInformation'])

        # Adding model 'Vat'
        db.create_table('billing_vat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('value', self.gf('django.db.models.fields.DecimalField')(default='19.6', max_digits=4, decimal_places=2)),
            ('is_default', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_custom', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('billing', ['Vat'])

        # Adding model 'Line'
        db.create_table('billing_line', (
            ('cremeentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['creme_core.CremeEntity'], unique=True, primary_key=True)),
            ('on_the_fly_item', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('quantity', self.gf('django.db.models.fields.DecimalField')(default='1.00', max_digits=10, decimal_places=2)),
            ('unit_price', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=10, decimal_places=2)),
            ('unit', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('discount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=10, decimal_places=2)),
            ('discount_unit', self.gf('django.db.models.fields.PositiveIntegerField')(default=1, null=True, blank=True)),
            ('total_discount', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('vat_value', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.Vat'], null=True, on_delete=models.PROTECT, blank=True)),
            ('type', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('billing', ['Line'])

        # Adding model 'ProductLine'
        db.create_table('billing_productline', (
            ('line_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Line'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('billing', ['ProductLine'])

        # Adding model 'ServiceLine'
        db.create_table('billing_serviceline', (
            ('line_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Line'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('billing', ['ServiceLine'])

        # Adding model 'ConfigBillingAlgo'
        db.create_table('billing_configbillingalgo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Organisation'])),
            ('name_algo', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('billing', ['ConfigBillingAlgo'])

        # Adding model 'SimpleBillingAlgo'
        db.create_table('billing_simplebillingalgo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('organisation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['persons.Organisation'])),
            ('last_number', self.gf('django.db.models.fields.IntegerField')()),
            ('prefix', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
        ))
        db.send_create_signal('billing', ['SimpleBillingAlgo'])

        # Adding unique constraint on 'SimpleBillingAlgo', fields ['organisation', 'last_number', 'ct']
        db.create_unique('billing_simplebillingalgo', ['organisation_id', 'last_number', 'ct_id'])

        # Adding model 'Base'
        db.create_table('billing_base', (
            ('cremeentity_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['creme_core.CremeEntity'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('number', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('issuing_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('expiration_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('discount', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=10, decimal_places=2)),
            ('billing_address', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='BillingAddress_set', null=True, to=orm['persons.Address'])),
            ('shipping_address', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='ShippingAddress_set', null=True, to=orm['persons.Address'])),
            ('currency', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='Currency_set', on_delete=models.PROTECT, to=orm['creme_core.Currency'])),
            ('comment', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('total_vat', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=14, decimal_places=2, blank=True)),
            ('total_no_vat', self.gf('django.db.models.fields.DecimalField')(default=0, null=True, max_digits=14, decimal_places=2, blank=True)),
            ('additional_info', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='AdditionalInformation_set', null=True, on_delete=models.SET_NULL, to=orm['billing.AdditionalInformation'])),
            ('payment_terms', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='PaymentTerms_set', null=True, on_delete=models.SET_NULL, to=orm['billing.PaymentTerms'])),
            ('payment_info', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.PaymentInformation'], null=True, blank=True)),
        ))
        db.send_create_signal('billing', ['Base'])

        # Adding model 'TemplateBase'
        db.create_table('billing_templatebase', (
            ('base_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Base'], unique=True, primary_key=True)),
            ('ct', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('status_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('billing', ['TemplateBase'])

        # Adding model 'SalesOrder'
        db.create_table('billing_salesorder', (
            ('base_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Base'], unique=True, primary_key=True)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.SalesOrderStatus'], on_delete=models.PROTECT)),
        ))
        db.send_create_signal('billing', ['SalesOrder'])

        # Adding model 'Quote'
        db.create_table('billing_quote', (
            ('base_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Base'], unique=True, primary_key=True)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.QuoteStatus'], on_delete=models.PROTECT)),
        ))
        db.send_create_signal('billing', ['Quote'])

        # Adding model 'Invoice'
        db.create_table('billing_invoice', (
            ('base_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Base'], unique=True, primary_key=True)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.InvoiceStatus'], on_delete=models.PROTECT)),
            ('payment_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.SettlementTerms'], null=True, blank=True)),
        ))
        db.send_create_signal('billing', ['Invoice'])

        # Adding model 'CreditNote'
        db.create_table('billing_creditnote', (
            ('base_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['billing.Base'], unique=True, primary_key=True)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['billing.CreditNoteStatus'], on_delete=models.PROTECT)),
        ))
        db.send_create_signal('billing', ['CreditNote'])

    def backwards(self, orm):
        # Removing unique constraint on 'SimpleBillingAlgo', fields ['organisation', 'last_number', 'ct']
        db.delete_unique('billing_simplebillingalgo', ['organisation_id', 'last_number', 'ct_id'])

        # Deleting model 'SettlementTerms'
        db.delete_table('billing_settlementterms')

        # Deleting model 'InvoiceStatus'
        db.delete_table('billing_invoicestatus')

        # Deleting model 'QuoteStatus'
        db.delete_table('billing_quotestatus')

        # Deleting model 'SalesOrderStatus'
        db.delete_table('billing_salesorderstatus')

        # Deleting model 'CreditNoteStatus'
        db.delete_table('billing_creditnotestatus')

        # Deleting model 'AdditionalInformation'
        db.delete_table('billing_additionalinformation')

        # Deleting model 'PaymentTerms'
        db.delete_table('billing_paymentterms')

        # Deleting model 'PaymentInformation'
        db.delete_table('billing_paymentinformation')

        # Deleting model 'Vat'
        db.delete_table('billing_vat')

        # Deleting model 'Line'
        db.delete_table('billing_line')

        # Deleting model 'ProductLine'
        db.delete_table('billing_productline')

        # Deleting model 'ServiceLine'
        db.delete_table('billing_serviceline')

        # Deleting model 'ConfigBillingAlgo'
        db.delete_table('billing_configbillingalgo')

        # Deleting model 'SimpleBillingAlgo'
        db.delete_table('billing_simplebillingalgo')

        # Deleting model 'Base'
        db.delete_table('billing_base')

        # Deleting model 'TemplateBase'
        db.delete_table('billing_templatebase')

        # Deleting model 'SalesOrder'
        db.delete_table('billing_salesorder')

        # Deleting model 'Quote'
        db.delete_table('billing_quote')

        # Deleting model 'Invoice'
        db.delete_table('billing_invoice')

        # Deleting model 'CreditNote'
        db.delete_table('billing_creditnote')

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_team': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['creme_core.UserRole']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'billing.additionalinformation': {
            'Meta': {'object_name': 'AdditionalInformation'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'billing.base': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Base', '_ormbases': ['creme_core.CremeEntity']},
            'additional_info': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'AdditionalInformation_set'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['billing.AdditionalInformation']"}),
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'BillingAddress_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'default': '1', 'related_name': "'Currency_set'", 'on_delete': 'models.PROTECT', 'to': "orm['creme_core.Currency']"}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '10', 'decimal_places': '2'}),
            'expiration_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'issuing_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'payment_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.PaymentInformation']", 'null': 'True', 'blank': 'True'}),
            'payment_terms': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'PaymentTerms_set'", 'null': 'True', 'on_delete': 'models.SET_NULL', 'to': "orm['billing.PaymentTerms']"}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'ShippingAddress_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'total_no_vat': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'}),
            'total_vat': ('django.db.models.fields.DecimalField', [], {'default': '0', 'null': 'True', 'max_digits': '14', 'decimal_places': '2', 'blank': 'True'})
        },
        'billing.configbillingalgo': {
            'Meta': {'object_name': 'ConfigBillingAlgo'},
            'ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name_algo': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Organisation']"})
        },
        'billing.creditnote': {
            'Meta': {'ordering': "('id',)", 'object_name': 'CreditNote', '_ormbases': ['billing.Base']},
            'base_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Base']", 'unique': 'True', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.CreditNoteStatus']", 'on_delete': 'models.PROTECT'})
        },
        'billing.creditnotestatus': {
            'Meta': {'ordering': "('order',)", 'object_name': 'CreditNoteStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'billing.invoice': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Invoice', '_ormbases': ['billing.Base']},
            'base_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Base']", 'unique': 'True', 'primary_key': 'True'}),
            'payment_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.SettlementTerms']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.InvoiceStatus']", 'on_delete': 'models.PROTECT'})
        },
        'billing.invoicestatus': {
            'Meta': {'ordering': "('order',)", 'object_name': 'InvoiceStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'billing.line': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Line', '_ormbases': ['creme_core.CremeEntity']},
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'discount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '10', 'decimal_places': '2'}),
            'discount_unit': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1', 'null': 'True', 'blank': 'True'}),
            'on_the_fly_item': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'quantity': ('django.db.models.fields.DecimalField', [], {'default': "'1.00'", 'max_digits': '10', 'decimal_places': '2'}),
            'total_discount': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'unit_price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '10', 'decimal_places': '2'}),
            'vat_value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.Vat']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'})
        },
        'billing.paymentinformation': {
            'Meta': {'object_name': 'PaymentInformation'},
            'account_number': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'bank_code': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'banking_domiciliation': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'bic': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'counter_code': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'}),
            'iban': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'PaymentInformationOrganisation_set'", 'to': "orm['persons.Organisation']"}),
            'rib_key': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True', 'blank': 'True'})
        },
        'billing.paymentterms': {
            'Meta': {'object_name': 'PaymentTerms'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'billing.productline': {
            'Meta': {'ordering': "('id',)", 'object_name': 'ProductLine', '_ormbases': ['billing.Line']},
            'line_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Line']", 'unique': 'True', 'primary_key': 'True'})
        },
        'billing.quote': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Quote', '_ormbases': ['billing.Base']},
            'base_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Base']", 'unique': 'True', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.QuoteStatus']", 'on_delete': 'models.PROTECT'})
        },
        'billing.quotestatus': {
            'Meta': {'ordering': "('order',)", 'object_name': 'QuoteStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'billing.salesorder': {
            'Meta': {'ordering': "('id',)", 'object_name': 'SalesOrder', '_ormbases': ['billing.Base']},
            'base_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Base']", 'unique': 'True', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['billing.SalesOrderStatus']", 'on_delete': 'models.PROTECT'})
        },
        'billing.salesorderstatus': {
            'Meta': {'ordering': "('order',)", 'object_name': 'SalesOrderStatus'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'order': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'billing.serviceline': {
            'Meta': {'ordering': "('id',)", 'object_name': 'ServiceLine', '_ormbases': ['billing.Line']},
            'line_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Line']", 'unique': 'True', 'primary_key': 'True'})
        },
        'billing.settlementterms': {
            'Meta': {'object_name': 'SettlementTerms'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'billing.simplebillingalgo': {
            'Meta': {'unique_together': "(('organisation', 'last_number', 'ct'),)", 'object_name': 'SimpleBillingAlgo'},
            'ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_number': ('django.db.models.fields.IntegerField', [], {}),
            'organisation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Organisation']"}),
            'prefix': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        'billing.templatebase': {
            'Meta': {'ordering': "('id',)", 'object_name': 'TemplateBase', '_ormbases': ['billing.Base']},
            'base_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['billing.Base']", 'unique': 'True', 'primary_key': 'True'}),
            'ct': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'status_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'billing.vat': {
            'Meta': {'object_name': 'Vat'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'value': ('django.db.models.fields.DecimalField', [], {'default': "'19.6'", 'max_digits': '4', 'decimal_places': '2'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'creme_core.cremeentity': {
            'Meta': {'ordering': "('id',)", 'object_name': 'CremeEntity'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'entity_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'header_filter_search_field': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_actived': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'creme_core.currency': {
            'Meta': {'object_name': 'Currency'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'international_symbol': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'local_symbol': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'creme_core.userrole': {
            'Meta': {'object_name': 'UserRole'},
            'creatable_ctypes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles_allowing_creation'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'exportable_ctypes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'roles_allowing_export'", 'null': 'True', 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'raw_admin_4_apps': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'raw_allowed_apps': ('django.db.models.fields.TextField', [], {'default': "''"})
        },
        'media_managers.image': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Image', '_ormbases': ['creme_core.CremeEntity']},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'Image_media_category_set'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['media_managers.MediaCategory']"}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '500'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'})
        },
        'media_managers.mediacategory': {
            'Meta': {'object_name': 'MediaCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_custom': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.address': {
            'Meta': {'object_name': 'Address'},
            'address': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'object_set'", 'to': "orm['contenttypes.ContentType']"}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'po_box': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'persons.legalform': {
            'Meta': {'object_name': 'LegalForm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.organisation': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Organisation', '_ormbases': ['creme_core.CremeEntity']},
            'annual_revenue': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'billing_address_orga_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'capital': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['media_managers.Image']", 'null': 'True', 'blank': 'True'}),
            'legal_form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.LegalForm']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'naf': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'rcs': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Sector']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_address_orga_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'siren': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'siret': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'staff_size': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.StaffSize']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'subject_to_vat': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tvaintra': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url_site': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'persons.sector': {
            'Meta': {'object_name': 'Sector'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.staffsize': {
            'Meta': {'object_name': 'StaffSize'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['billing']