# encoding: utf-8

import datetime

from south.db import db
from south.v2 import SchemaMigration

from django.db import models


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Deleting field 'EmailTemplate.use_rte'
        db.delete_column('emails_emailtemplate', 'use_rte')

        # Adding field 'EmailTemplate.body_html'
        db.add_column('emails_emailtemplate', 'body_html', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Deleting field 'LightWeightEmail.body_html'
        db.delete_column('emails_lightweightemail', 'body_html')

        # Deleting field 'LightWeightEmail.signature'
        db.delete_column('emails_lightweightemail', 'signature_id')

        # Removing M2M table for field attachments on 'LightWeightEmail'
        db.delete_table('emails_lightweightemail_attachments')

        # Changing field 'LightWeightEmail.sending'
        db.alter_column('emails_lightweightemail', 'sending_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['emails.EmailSending']))

        # Adding field 'EmailSending.body_html'
        db.add_column('emails_emailsending', 'body_html', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

    def backwards(self, orm):
        # Adding field 'EmailTemplate.use_rte'
        db.add_column('emails_emailtemplate', 'use_rte', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Deleting field 'EmailTemplate.body_html'
        db.delete_column('emails_emailtemplate', 'body_html')

        # Adding field 'LightWeightEmail.body_html'
        db.add_column('emails_lightweightemail', 'body_html', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'LightWeightEmail.signature'
        db.add_column('emails_lightweightemail', 'signature', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['emails.EmailSignature'], null=True, blank=True), keep_default=False)

        # Adding M2M table for field attachments on 'LightWeightEmail'
        db.create_table('emails_lightweightemail_attachments', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('lightweightemail', models.ForeignKey(orm['emails.lightweightemail'], null=False)),
            ('document', models.ForeignKey(orm['documents.document'], null=False))
        ))
        db.create_unique('emails_lightweightemail_attachments', ['lightweightemail_id', 'document_id'])

        # Changing field 'LightWeightEmail.sending'
        db.alter_column('emails_lightweightemail', 'sending_id', self.gf('django.db.models.fields.related.ForeignKey')(null=True, to=orm['emails.EmailSending']))

        # Deleting field 'EmailSending.body_html'
        db.delete_column('emails_emailsending', 'body_html')


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
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['creme_core.UserRole']", 'null': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
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
        'creme_core.language': {
            'Meta': {'object_name': 'Language'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
        'documents.document': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Document', '_ormbases': ['creme_core.CremeEntity']},
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filedata': ('django.db.models.fields.files.FileField', [], {'max_length': '500'}),
            'folder': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['documents.Folder']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'documents.folder': {
            'Meta': {'ordering': "('id',)", 'object_name': 'Folder', '_ormbases': ['creme_core.CremeEntity']},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'folder_category_set'", 'null': 'True', 'to': "orm['documents.FolderCategory']"}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'parent_folder': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'parent_folder_set'", 'null': 'True', 'to': "orm['documents.Folder']"}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'documents.foldercategory': {
            'Meta': {'object_name': 'FolderCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'emails.emailcampaign': {
            'Meta': {'ordering': "('id',)", 'object_name': 'EmailCampaign', '_ormbases': ['creme_core.CremeEntity']},
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'mailing_lists': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['emails.MailingList']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'emails.emailrecipient': {
            'Meta': {'object_name': 'EmailRecipient'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ml': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['emails.MailingList']"})
        },
        'emails.emailsending': {
            'Meta': {'object_name': 'EmailSending'},
            'attachments': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['documents.Document']", 'symmetrical': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'body_html': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sendings_set'", 'to': "orm['emails.EmailCampaign']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.EmailField', [], {'max_length': '100'}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {}),
            'signature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['emails.EmailSignature']", 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'emails.emailsignature': {
            'Meta': {'ordering': "('name',)", 'object_name': 'EmailSignature'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'images': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['media_managers.Image']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'emails.emailtemplate': {
            'Meta': {'ordering': "('id',)", 'object_name': 'EmailTemplate', '_ormbases': ['creme_core.CremeEntity']},
            'attachments': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['documents.Document']", 'symmetrical': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'signature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['emails.EmailSignature']", 'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'emails.entityemail': {
            'Meta': {'object_name': 'EntityEmail', '_ormbases': ['creme_core.CremeEntity']},
            'attachments': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['documents.Document']", 'symmetrical': 'False'}),
            'body': ('django.db.models.fields.TextField', [], {}),
            'body_html': ('django.db.models.fields.TextField', [], {}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'D5hwk2mJAvIlFLqrUFQaEBZiGZ3vjo8F'", 'unique': 'True', 'max_length': '32'}),
            'reads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'reception_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'signature': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['emails.EmailSignature']", 'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'emails.lightweightemail': {
            'Meta': {'object_name': 'LightWeightEmail'},
            'body': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'reads': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'reception_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'recipient_entity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'received_lw_mails'", 'null': 'True', 'to': "orm['creme_core.CremeEntity']"}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sending': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mails_set'", 'to': "orm['emails.EmailSending']"}),
            'sending_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'emails.mailinglist': {
            'Meta': {'ordering': "('id',)", 'object_name': 'MailingList', '_ormbases': ['creme_core.CremeEntity']},
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'parents_set'", 'symmetrical': 'False', 'to': "orm['emails.MailingList']"}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['persons.Contact']", 'symmetrical': 'False'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'organisations': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['persons.Organisation']", 'symmetrical': 'False'})
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
        'persons.civility': {
            'Meta': {'object_name': 'Civility'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'persons.contact': {
            'Meta': {'ordering': "('last_name', 'first_name')", 'object_name': 'Contact', '_ormbases': ['creme_core.CremeEntity']},
            'billing_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'billing_address_contact_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'birthday': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'civility': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Civility']", 'null': 'True', 'blank': 'True'}),
            'cremeentity_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['creme_core.CremeEntity']", 'unique': 'True', 'primary_key': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'fax': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['media_managers.Image']", 'null': 'True', 'blank': 'True'}),
            'is_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'related_contact'", 'null': 'True', 'to': "orm['auth.User']"}),
            'language': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['creme_core.Language']", 'null': 'True', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Position']", 'null': 'True', 'blank': 'True'}),
            'sector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Sector']", 'null': 'True', 'blank': 'True'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_address_contact_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'skype': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url_site': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
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
            'legal_form': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.LegalForm']", 'null': 'True', 'blank': 'True'}),
            'naf': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'rcs': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'sector': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.Sector']", 'null': 'True', 'blank': 'True'}),
            'shipping_address': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'shipping_address_orga_set'", 'null': 'True', 'to': "orm['persons.Address']"}),
            'siren': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'siret': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'staff_size': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['persons.StaffSize']", 'null': 'True', 'blank': 'True'}),
            'subject_to_vat': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'tvaintra': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url_site': ('django.db.models.fields.URLField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'persons.position': {
            'Meta': {'object_name': 'Position'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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

    complete_apps = ['emails']
