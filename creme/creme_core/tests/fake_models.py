# -*- coding: utf-8 -*-

from django.conf import settings

if not settings.TESTS_ON:
    __all__ = ()
else:
    from decimal import Decimal

    from django.core.exceptions import ValidationError
    from django.db import models
    from django.utils.translation import ugettext_lazy as _, ugettext, pgettext_lazy

    from ..core.function_field import FunctionField, FunctionFieldResult, FunctionFieldResultsList
    from ..models import CremeModel, CremeEntity, Language
    from ..models.fields import PhoneField, BasicAutoField, MoneyField, DatePeriodField

    from .fake_constants import FAKE_DISCOUNT_UNIT, FAKE_PERCENT_UNIT


    class FakeFolderCategory(CremeModel):
        name = models.CharField(_(u'Category name'), max_length=100, unique=True)
#        is_custom = BooleanField(default=True).set_tags(viewable=False) #used by creme_config

        def __unicode__(self):
            return self.name

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Folder category'
            verbose_name_plural = u'test Folder categories'
            ordering = ('name',)


    class FakeFolder(CremeEntity):
        title     = models.CharField(_(u'Title'), max_length=100)
#        description   = models.TextField(_(u'Description'), null=True, blank=True).set_tags(optional=True)
        parent    = models.ForeignKey('self', verbose_name=_(u'Parent folder'),
                                      blank=True, null=True, related_name='children',
                                      # on_delete=PROTECT, ??
                                     )
        category  = models.ForeignKey(FakeFolderCategory, verbose_name=_(u'Category'),
                                      blank=True, null=True, on_delete=models.SET_NULL,
                                      # related_name='folder_category_set',
                                     )

#        allowed_related = CremeEntity.allowed_related | {'document'}
#        creation_label = _('Add a folder')

        class Meta:
            app_label = 'creme_core'
#            unique_together = ('title', 'folder', 'category')
            verbose_name = u'Test Folder'
            verbose_name_plural = u'Test Folders'
            ordering = ('title',)

        def __unicode__(self):
            return self.title


    class FakeDocument(CremeEntity):
        title       = models.CharField(_(u'Title'), max_length=100)
#        description = models.TextField(_(u'Description'), blank=True, null=True).set_tags(optional=True)
        filedata    = models.FileField(_(u'File'), max_length=100, upload_to='upload/creme_core-tests')
        folder      = models.ForeignKey(FakeFolder, verbose_name=_(u'Folder'), on_delete=models.PROTECT)

#        creation_label = _('Add a document')

        class Meta:
            app_label = 'creme_core'
            verbose_name = 'Test Document'
            verbose_name_plural = u'Test Documents'
            ordering = ('title',)

        def __unicode__(self):
            return u'%s - %s' % (self.folder, self.title)

#        def get_absolute_url(self):
#           return "/documents/document/%s" % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/documents'

#        def get_edit_absolute_url(self):
#            return "/documents/document/edit/%s" % self.id


    class FakeFileComponent(CremeModel):
        filedata = models.FileField(_(u'File'), max_length=100,
                                    upload_to='upload/creme_core-tests',
                                    null=True, blank=True,
                                   )

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test File component'
            verbose_name_plural = u'Test File components'


    class FakeImageCategory(CremeModel):
        name = models.CharField(_(u'Name'), max_length=100)

        def __unicode__(self):
            return self.name

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Image category'
            verbose_name_plural = u'Test Image categories'
            ordering = ('name',)


    class FakeImage(CremeEntity):
        name        = models.CharField(_(u'Name'), max_length=100, blank=True, null=True)
        description = models.TextField(_(u'Description'), blank=True, null=True)\
                            .set_tags(optional=True)
#        image       = ImageField(_('Image'), height_field='height', width_field='width',
#                                 upload_to='upload/images', max_length=500)
        filedata    = models.FileField(_(u'File'), max_length=100, editable=False,
                                       upload_to='upload/creme_core-tests',
                                      )
        categories  = models.ManyToManyField(FakeImageCategory,
                                             verbose_name=_(u'Categories'),
                                             related_name='+', blank=True,
                                            )
        exif_date   = models.DateField(_(u"Exif date"), blank=True, null=True)\
                            .set_tags(optional=True)

#        creation_label = _('Add an image')

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Image'
            verbose_name_plural = u'Test Images'
            ordering = ('name',)

        def __unicode__(self):
            return self.name

        def get_absolute_url(self):
            return '/tests/image/%s' % self.id

        @staticmethod
        def get_clone_absolute_url():
            return ''

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/images'

#        def get_edit_absolute_url(self):
#            return "/media_managers/image/edit/%s" % self.id


    class FakeCivility(CremeModel):
        title    = models.CharField(_(u'Title'), max_length=100)
        shortcut = models.CharField(_(u'Shortcut'), max_length=100)

        def __unicode__(self):
            return self.title

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test civility'
            verbose_name_plural = u'Test civilities'
            ordering = ('title',)


    class FakePosition(CremeModel):
        title = models.CharField(_(u'Title'), max_length=100)

        def __unicode__(self):
            return self.title

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test People position'
            verbose_name_plural = u'Test People positions'
            ordering = ('title',)


    class FakeSector(CremeModel):
        title     = models.CharField(_(u'Title'), max_length=100)
        is_custom = models.BooleanField(default=True).set_tags(viewable=False)  # Used by creme_config
        order     = BasicAutoField(_('Order'))  # Used by creme_config

        def __unicode__(self):
            return self.title

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test sector'
            verbose_name_plural = u'Test sectors'
            ordering = ('order',)


    class FakeAddress(CremeModel):
        value      = models.TextField(_(u"Address"), blank=True, null=True)
        zipcode    = models.CharField(_(u"Zip code"), max_length=100, blank=True, null=True) \
                           .set_tags(optional=True)
        city       = models.CharField(_(u"City"), max_length=100, blank=True, null=True)\
                           .set_tags(optional=True)
        department = models.CharField(_(u"Department"), max_length=100, blank=True, null=True)\
                           .set_tags(optional=True)
        country    = models.CharField(_(u"Country"), max_length=40, blank=True, null=True)\
                           .set_tags(optional=True)

        entity     = models.ForeignKey(CremeEntity, related_name='+', editable=False)\
                           .set_tags(viewable=False)

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test address'
            verbose_name_plural = u'Test addresses'

        def __unicode__(self):
            return  u' '.join(filter(None, [self.value, self.zipcode, self.city, self.department, self.country]))

        def get_edit_absolute_url(self):
            return '/tests/address/edit/%s' % self.id

        def get_related_entity(self):  # For generic views
            return self.entity


    class FakeContact(CremeEntity):
        civility    = models.ForeignKey(FakeCivility, verbose_name=_(u'Civility'),
                                        blank=True, null=True, on_delete=models.SET_NULL,
                                       )
        last_name   = models.CharField(_(u'Last name'), max_length=100)
        first_name  = models.CharField(_(u'First name'), max_length=100,
                                       blank=True, null=True,
                                      ).set_tags(optional=True)
        is_a_nerd   = models.BooleanField(_(u'Is a Nerd'), default=False)
        description = models.TextField(_(u'Description'), blank=True, null=True)\
                            .set_tags(optional=True)
        phone       = PhoneField(_(u'Phone number'), max_length=100,
                                 blank=True, null=True,
                                ).set_tags(optional=True)
        mobile      = PhoneField(_(u'Mobile'), max_length=100,
                                 blank=True, null=True,
                                ).set_tags(optional=True)
        position    = models.ForeignKey(FakePosition, verbose_name=_(u'Position'),
                                        blank=True, null=True, on_delete=models.SET_NULL,
                                       ).set_tags(optional=True)
        sector      = models.ForeignKey(FakeSector, verbose_name=_(u'Line of business'),
                                        blank=True, null=True, on_delete=models.SET_NULL,
                                       ).set_tags(optional=True)
        email       = models.EmailField(_(u'Email address'), max_length=100, blank=True, null=True)
        url_site    = models.URLField(_(u'Web Site'), max_length=500, blank=True, null=True)
        languages   = models.ManyToManyField(Language, verbose_name=_(u'Spoken language(s)'), blank=True)
        address     = models.ForeignKey(FakeAddress, verbose_name=_(u'Billing address'),
                                        blank=True, null=True,  editable=False,
                                        related_name='+',
                                       ).set_tags(enumerable=False)  # clonable=False useless
        is_user     = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_(u'Related user'),
                                        blank=True, null=True, editable=False,
                                        related_name='+',
                                        on_delete=models.SET_NULL,
                                       ).set_tags(clonable=False, enumerable=False)\
                                        .set_null_label(pgettext_lazy('persons-is_user', u'None'))
        birthday    = models.DateField(_(u'Birthday'), blank=True, null=True)\
                            .set_tags(optional=True)
        image       = models.ForeignKey(FakeImage, verbose_name=_(u'Photograph'),
                                        blank=True, null=True, on_delete=models.SET_NULL,
                                       ).set_tags(optional=True)

#        creation_label = _('Add a contact')

        class Meta:
            app_label = 'creme_core'
            ordering = ('last_name', 'first_name')
            verbose_name = u'Test Contact'
            verbose_name_plural = u'Test Contacts'
            index_together = ('last_name', 'first_name', 'cremeentity_ptr')

        def __unicode__(self):
            return u'%s %s' % (self.first_name, self.last_name)

        def clean(self):
            if self.is_user_id and not self.first_name:
                raise ValidationError(ugettext('This Contact is related to a user and must have a first name.'))

        def get_absolute_url(self):
            return '/tests/contact/%s' % self.id

        def get_edit_absolute_url(self):
            return '/tests/contact/edit/%s' % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/contacts'


    class FakeLegalForm(CremeModel):
        title = models.CharField(_(u'Title'), max_length=100)

        def __unicode__(self):
            return self.title

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test legal form'
            verbose_name_plural = u'Test Legal forms'
            ordering = ('title',)


    class _GetFakeTodos(FunctionField):
        name         = 'tests-get_fake_todos'
        verbose_name = _(u"Fake Todos")
        # has_filter   = False #==> cannot search

        def __call__(self, entity):
            return FunctionFieldResultsList(FunctionFieldResult('Todo %s #%s' % (entity, i))
                                                for i in xrange(1, 3)
                                        )


    class FakeOrganisation(CremeEntity):
        name            = models.CharField(_(u'Name'), max_length=200)
        phone           = PhoneField(_(u'Phone number'), max_length=100,
                                     blank=True, null=True,
                                    )
        email           = models.EmailField(_(u'Email address'), max_length=100,
                                            blank=True, null=True,
                                           )
        url_site        = models.URLField(_(u'Web Site'), max_length=500,
                                          blank=True, null=True,
                                         ).set_tags(optional=True)
        sector          = models.ForeignKey(FakeSector, verbose_name=_(u'Sector'),
                                            blank=True, null=True, on_delete=models.SET_NULL,
                                          ).set_tags(optional=True)
        capital         = models.PositiveIntegerField(_(u'Capital'), blank=True, null=True)\
                                .set_tags(optional=True)
        subject_to_vat  = models.BooleanField(_(u'Subject to VAT'), default=True)
        legal_form      = models.ForeignKey(FakeLegalForm, verbose_name=_(u'Legal form'),
                                            blank=True, null=True, on_delete=models.SET_NULL,
                                           )
        address         = models.ForeignKey(FakeAddress, verbose_name=_(u'Billing address'),
                                            blank=True, null=True, editable=False,
                                            related_name='+',
                                           ).set_tags(enumerable=False) #clonable=False useless
        description     = models.TextField(_(u'Description'), blank=True, null=True)
        creation_date   = models.DateField(_(u'Date of creation'), blank=True, null=True)
        image           = models.ForeignKey(FakeImage, verbose_name=_(u'Logo'),
                                            blank=True, null=True, on_delete=models.SET_NULL,
                                           )

        function_fields = CremeEntity.function_fields.new(_GetFakeTodos())

#        creation_label = _('Add an organisation')

        class Meta:
            app_label = 'creme_core'
            ordering = ('name',)
            verbose_name = u'Test Organisation'
            verbose_name_plural = u'Test Organisations'
            index_together = ('name', 'cremeentity_ptr')

        def __unicode__(self):
            return self.name

        def get_absolute_url(self):
            return '/tests/organisation/%s' % self.id

        def get_edit_absolute_url(self):
            return '/tests/organisation/edit/%s' % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/organisations'


    class FakeActivityType(CremeModel):
        name  = models.CharField(_(u'Name'), max_length=100, unique=True)
        order = BasicAutoField(_('Order'))  # Used by creme_config

        class Meta:
            app_label = 'creme_core'
            verbose_name = u"Test Type of activity"
            verbose_name_plural = u"Test Types of activity"
            ordering = ('name',)


    class FakeActivity(CremeEntity):
        title = models.CharField(_(u'Title'), max_length=100, unique=True)
        start = models.DateTimeField(_(u'Start'), blank=True, null=True)
        end   = models.DateTimeField(_(u'End'), blank=True, null=True)
        type  = models.ForeignKey(FakeActivityType, verbose_name=_(u'Activity type'),
                                  on_delete=models.PROTECT,  # editable=False,
                                 )

#        creation_label = _('Add an activity')

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Activity'
            verbose_name_plural = u'Test Activities'
            ordering = ('-start',)

        def __unicode__(self):
            return self.title

#        def get_absolute_url(self):
#            return "/activities/activity/%s" % self.id

#        def get_edit_absolute_url(self):
#            return "/activities/activity/edit/%s" % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/activities'


    class FakeMailingList(CremeEntity):
        name = models.CharField(_(u'Name of the mailing list'), max_length=80)

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Mailing list'
            verbose_name_plural = u'Test Mailing lists'
            ordering = ('name',)

        def __unicode__(self) :
            return self.name

#        def get_absolute_url(self):
#            return "/emails/mailing_list/%s" % self.id

#        def get_edit_absolute_url(self):
#            return "/emails/mailing_list/edit/%s" % self.id

#        @staticmethod
#        def get_lv_absolute_url():
#            return "/emails/mailing_lists"


    class FakeEmailCampaign(CremeEntity):
        name          = models.CharField(_(u'Name of the campaign'), max_length=100, blank=False, null=False)
        mailing_lists = models.ManyToManyField(FakeMailingList, verbose_name=_(u'Related mailing lists'))

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test campaign'
            verbose_name_plural = u'Test campaigns'
            ordering = ('name',)

        def __unicode__(self):
            return self.name

#        def get_absolute_url(self):
#            return "/emails/campaign/%s" % self.id

#        def get_edit_absolute_url(self):
#            return "/emails/campaign/edit/%s" % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/e_campaigns'


    class FakeInvoice(CremeEntity):
        name             = models.CharField(_(u'Name'), max_length=100)
        number           = models.CharField(_(u'Number'), max_length=100, blank=True, null=True)
        issuing_date     = models.DateField(_(u"Issuing date"), blank=True, null=True)
        expiration_date  = models.DateField(_(u"Expiration date"), blank=True, null=True)\
                                 .set_tags(optional=True)
        periodicity      = DatePeriodField(_(u'Periodicity of the generation'), blank=True, null=True)
        total_vat        = MoneyField(_(u'Total with VAT'), max_digits=14, decimal_places=2,
                                      blank=True, null=True, editable=False, default=0,
                                     )
        total_no_vat     = MoneyField(_(u'Total without VAT'), max_digits=14, decimal_places=2,
                                      blank=True, null=True, editable=False, default=0,
                                     ).set_tags(optional=True)

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Invoice'
            verbose_name_plural = u'Test Invoices'
            # ordering = ('name',)
            ordering = ('name', '-expiration_date')

        def __unicode__(self):
            return self.name

        def get_absolute_url(self):
            return '/tests/invoice/%s' % self.id

#        def get_edit_absolute_url(self):
#            return "/billing/invoice/edit/%s" % self.id

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/invoices'


    class FakeInvoiceLine(CremeEntity):
        invoice       = models.ForeignKey(FakeInvoice)
        item          = models.CharField(u'Item', max_length=100, blank=True, null=True)
        quantity      = models.DecimalField(_(u'Quantity'),
                                            max_digits=10, decimal_places=2,
                                            default=Decimal('1.00'),
                                           )
        unit_price    = models.DecimalField(_(u'Unit price'), default=Decimal(),
                                            max_digits=10, decimal_places=2,
                                           )
        discount      = models.DecimalField(_(u'Discount'), default=Decimal(),
                                            max_digits=10, decimal_places=2,
                                           )
        discount_unit = models.PositiveIntegerField(_(u'Discount Unit'),
                                                    blank=True, null=True,
                                                    choices=FAKE_DISCOUNT_UNIT.items(),
                                                    default=FAKE_PERCENT_UNIT,
                                                   )

        class Meta:
            app_label = 'creme_core'
            verbose_name = u'Test Invoice Line'
            verbose_name_plural = u'Test Invoice Lines'
            ordering = ('created',)

        @staticmethod
        def get_lv_absolute_url():
            return '/tests/invoice_lines'

        def get_related_entity(self):  # For generic views & delete
            return self.invoice
