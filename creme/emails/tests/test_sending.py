# -*- coding: utf-8 -*-

try:
    from functools import partial
    from datetime import timedelta # datetime
    from pickle import loads

    from django.contrib.contenttypes.models import ContentType
    from django.core import mail as django_mail
    from django.test.utils import override_settings
    from django.utils.timezone import now, make_naive, get_current_timezone
    from django.utils.translation import ugettext as _

    from creme.creme_core.models import SetCredentials, SettingValue
    from creme.creme_core.auth.entity_credentials import EntityCredentials

    # from creme.persons.models import Contact, Organisation
    from creme.persons.tests.base import skipIfCustomContact, skipIfCustomOrganisation

    from .base import (_EmailsTestCase, skipIfCustomEmailCampaign,
            skipIfCustomEmailTemplate, skipIfCustomMailingList,
            Contact, Organisation, EmailCampaign, EmailTemplate, MailingList)
    from ..constants import SETTING_EMAILCAMPAIGN_SENDER, MAIL_STATUS_NOTSENT
    from ..management.commands.emails_send import Command as EmailsSendCommand
    from ..models import EmailSending, EmailRecipient, LightWeightEmail  # EmailCampaign EmailTemplate MailingList
    from ..models.sending import (SENDING_TYPE_IMMEDIATE, SENDING_TYPE_DEFERRED,
            SENDING_STATE_DONE, SENDING_STATE_PLANNED)
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


@skipIfCustomEmailCampaign
@skipIfCustomEmailTemplate
@skipIfCustomMailingList
class SendingsTestCase(_EmailsTestCase):
    def _load_or_fail(self, data):
        with self.assertNoException():
            return loads(data.encode('utf-8'))

    def _build_add_url(self, campaign):
        return '/emails/campaign/%s/sending/add' % campaign.id

    def repopulate_email(self):
        SettingValue.objects.filter(key_id=SETTING_EMAILCAMPAIGN_SENDER).delete()
        self.populate('emails')

    def test_sender_setting01(self):
        self.repopulate_email()
        user = self.login()
        camp = EmailCampaign.objects.create(user=user, name='camp01')
        template = EmailTemplate.objects.create(user=user, name='name',
                                                subject='SUBJECT', body='BODY',
                                               )

        url = self._build_add_url(camp)
        response = self.assertGET200(url)

        with self.assertNoException():
            sender = response.context['form'].fields['sender']

        self.assertIsNone(sender.initial)
        sender_email = 'vicious@reddragons.mrs'
        self.assertNoFormError(self.client.post(url, data={'sender':   sender_email,
                                                           'type':     SENDING_TYPE_IMMEDIATE,
                                                           'template': template.id,
                                                          }
                                               )
                              )
        response = self.assertGET200(url)

        with self.assertNoException():
            sender = response.context['form'].fields['sender']

        self.assertEqual(sender_email, sender.initial)

        response = self.assertPOST200(url, data={'sender':   u"another_email@address.com",
                                                 'type':     SENDING_TYPE_IMMEDIATE,
                                                 'template': template.id,
                                                }
                                     )
        self.assertFormError(response, 'form', 'sender',
                             _(u"You are not allowed to modify the sender address, please contact your administrator."))

    def test_sender_setting02(self):
        self.repopulate_email()
        user = self.login(is_superuser=False,
                   allowed_apps=('emails',),
                   creatable_models=(EmailSending, EmailCampaign)
                  )
        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW | EntityCredentials.DELETE |
                                            EntityCredentials.LINK | EntityCredentials.UNLINK |
                                            EntityCredentials.CHANGE,
                                      set_type=SetCredentials.ESET_ALL
                                     )

        camp = EmailCampaign.objects.create(user=user, name='camp01')
        template = EmailTemplate.objects.create(user=user, name='name',
                                                subject='SUBJECT', body='BODY',
                                               )

        url = self._build_add_url(camp)
        response = self.assertGET200(url)

        with self.assertNoException():
            sender = response.context['form'].fields['sender']

        self.assertEqual(
            _(u"No sender email address has been configured, please contact your administrator."),
            sender.initial)
        sender_email = 'vicious@reddragons.mrs'

        response = self.client.post(url, data={'sender':   sender_email,
                                               'type':     SENDING_TYPE_IMMEDIATE,
                                               'template': template.id,
                                              }
                                   )
        self.assertFormError(response, 'form', 'sender',
                             _(u"You are not allowed to modify the sender address, please contact your administrator."))

        sender_setting = SettingValue.objects.get(key_id=SETTING_EMAILCAMPAIGN_SENDER)
        sender_setting.value = sender_email
        sender_setting.save()

        response = self.assertGET200(url)

        with self.assertNoException():
            sender = response.context['form'].fields['sender']

        self.assertEqual(sender_email, sender.initial)

        self.assertNoFormError(self.client.post(url, data={'sender':   sender_email,
                                                           'type':     SENDING_TYPE_IMMEDIATE,
                                                           'template': template.id,
                                                          }
                                               )
                              )

    @skipIfCustomContact
    @skipIfCustomOrganisation
    def test_create01(self):
        user = self.login()
        # We create voluntarily duplicates (recipients that have same addresses
        # than Contact/Organisation, MailingList that contain the same addresses)
        # EmailSending should not contain duplicates.
        camp = EmailCampaign.objects.create(user=user, name='camp01')

        self.assertFalse(camp.sendings_set.exists())

        create_ml = partial(MailingList.objects.create, user=user)
        mlist01 = create_ml(name='ml01')
        mlist02 = create_ml(name='ml02')
        mlist03 = create_ml(name='ml03')
        mlist04 = create_ml(name='ml04', is_deleted=True)
        mlist05 = create_ml(name='ml05')
        mlist06 = create_ml(name='ml06', is_deleted=True)

        mlist01.children.add(mlist02, mlist03, mlist04)
        camp.mailing_lists.add(mlist01, mlist05, mlist06)

        addresses = ['spike.spiegel@bebop.com',  # 0
                     'jet.black@bebop.com',      # 1
                     'faye.valentine@bebop.com', # 2
                     'ed.wong@bebop.com',        # 3
                     'ein@bebop.com',            # 4
                     'contact@nerv.jp',          # 5
                     'contact@seele.jp',         # 6
                     'shin@reddragons.mrs',      # 7
                    ]

        create_recipient = EmailRecipient.objects.create
        create_recipient(ml=mlist01, address=addresses[0])
        create_recipient(ml=mlist02, address=addresses[2])
        create_recipient(ml=mlist02, address=addresses[3])
        create_recipient(ml=mlist03, address=addresses[3])
        create_recipient(ml=mlist03, address=addresses[4])
        create_recipient(ml=mlist03, address=addresses[6])
        create_recipient(ml=mlist04, address='vicious@reddragons.mrs')
        create_recipient(ml=mlist05, address=addresses[7])
        create_recipient(ml=mlist06, address='jin@reddragons.mrs')

        create_contact = partial(Contact.objects.create, user=user)
        contacts = [create_contact(first_name='Spike', last_name='Spiegel', email=addresses[0]),
                    create_contact(first_name='Jet',   last_name='Black',   email=addresses[1]),
                   ]
        deleted_contact = create_contact(first_name='Ed', last_name='Wong',
                                         email='ew@bebop.com', is_deleted=True,
                                        )

        mlist01.contacts.add(contacts[0])
        mlist02.contacts.add(contacts[0])
        mlist02.contacts.add(contacts[1])
        mlist02.contacts.add(deleted_contact)

        create_orga = partial(Organisation.objects.create, user=user)
        orgas = [create_orga(name='NERV',  email=addresses[5]),
                 create_orga(name='Seele', email=addresses[6]),
                ]

        mlist02.organisations.add(orgas[0])
        mlist03.organisations.add(orgas[0])
        mlist03.organisations.add(orgas[1])

        subject = 'SUBJECT'
        body    = 'BODYYYYYYYYYYY'
        template = EmailTemplate.objects.create(user=user, name='name', subject=subject, body=body)

        url = self._build_add_url(camp)
        self.assertGET200(url)

        self.assertNoFormError(self.client.post(url, data={'sender':   'vicious@reddragons.mrs',
                                                           'type':     SENDING_TYPE_IMMEDIATE,
                                                           'template': template.id,
                                                          }
                                               )
                              )

        sendings = EmailCampaign.objects.get(pk=camp.id).sendings_set.all()
        self.assertEqual(1, len(sendings))

        sending = sendings[0]
        self.assertEqual(SENDING_TYPE_IMMEDIATE, sending.type)
        self.assertEqual(SENDING_STATE_PLANNED,  sending.state)
        self.assertEqual(subject,                sending.subject)
        self.assertEqual(body,                   sending.body)
        self.assertEqual('',                     sending.body_html)

        mails = sending.mails_set.all()
        self.assertEqual(len(addresses), len(mails))

        addr_set = {mail.recipient for mail in mails}
        self.assertTrue(all(address in addr_set for address in addresses))

        related_set = {mail.recipient_entity_id for mail in mails}
        self.assertTrue(all(c.id in related_set for c in contacts))
        self.assertTrue(all(o.id in related_set for o in orgas))


        self.assertEqual('', sending.mails_set.filter(recipient_entity=None)[0].body)
        self.assertEqual('', sending.mails_set.get(recipient_entity=contacts[0].id).body)
        self.assertEqual('', sending.mails_set.get(recipient_entity=orgas[0].id).body)

        mail = mails[0]
        self.assertEqual(0, mail.reads)
        self.assertEqual(MAIL_STATUS_NOTSENT, mail.status)
        self.assertGET200('/emails/mails_history/%s' % mail.id)

        response = self.assertGET200('/emails/mail/get_body/%s' % mail.id)
        self.assertEqual(u'', response.content)

        #popup detail view -----------------------------------------------------
        response = self.assertPOST200('/emails/campaign/sending/%s' % sending.id)
        self.assertContains(response, contacts[0].email)
        self.assertContains(response, orgas[0].email)

        #test delete campaign --------------------------------------------------
        camp.trash()
        response = self.assertPOST(302, '/creme_core/entity/delete/%s' % camp.id)
        self.assertFalse(EmailCampaign.objects.exists())
        self.assertFalse(EmailSending.objects.exists())
        self.assertFalse(LightWeightEmail.objects.exists())

    @skipIfCustomContact
    def test_create02(self):
        "Test template"
        user = self.login()
        first_name = 'Spike'
        last_name  = 'Spiegel'

        camp    = EmailCampaign.objects.create(user=user, name='camp01')
        mlist   = MailingList.objects.create(user=user, name='ml01')
        contact = Contact.objects.create(user=user, first_name=first_name,
                                         last_name=last_name, email='spike.spiegel@bebop.com',
                                        )

        camp.mailing_lists.add(mlist)
        mlist.contacts.add(contact)

        subject = 'Hello'
        body    = 'Your first name is: {{first_name}} !'
        body_html = '<p>Your last name is: {{last_name}} !</p>'
        template = EmailTemplate.objects.create(user=user, name='name', subject=subject,
                                                body=body, body_html=body_html,
                                               )
        response = self.client.post(self._build_add_url(camp),
                                    data = {'sender':   'vicious@reddragons.mrs',
                                            'type':     SENDING_TYPE_IMMEDIATE,
                                            'template': template.id,
                                           }
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            sending = self.refresh(camp).sendings_set.all()[0]

        self.assertEqual(sending.subject, subject)

        with self.assertNoException():
            mail = sending.mails_set.all()[0]

        self.assertEqual('Your first name is: %s !' % first_name, mail.get_body())

        rendered_body = '<p>Your last name is: %s !</p>' % last_name
        self.assertEqual(rendered_body, mail.get_body_html())
        self.assertEqual(rendered_body, self.client.get('/emails/mail/get_body/%s' % mail.id).content)

        #test delete sending ---------------------------------------------------
        ct = ContentType.objects.get_for_model(EmailSending)
        self.assertPOST(302, '/creme_core/entity/delete_related/%s' % ct.id, data={'id': sending.pk})
        self.assertDoesNotExist(sending)
        self.assertDoesNotExist(mail)

    @skipIfCustomContact
    @skipIfCustomOrganisation
    @override_settings(EMAILCAMPAIGN_SLEEP_TIME=0.1)
    def test_create03(self):
        "Command + outbox"
        user = self.login()
        camp     = EmailCampaign.objects.create(user=user, name='camp01')
        template = EmailTemplate.objects.create(user=user, name='name', subject='subject', body='body')
        mlist    = MailingList.objects.create(user=user, name='ml01')
        contact  = Contact.objects.create(user=user, email='spike.spiegel@bebop.com',
                                          first_name='Spike', last_name='Spiegel',
                                         )

        create_orga = partial(Organisation.objects.create, user=user)
        orga1 = create_orga(name='NERV',  email='contact@nerv.jp')
        orga2 = create_orga(name='Seele', email='contact@seele.jp')

        camp.mailing_lists.add(mlist)
        mlist.contacts.add(contact)
        mlist.organisations.add(orga1, orga2)

        sender = 'vicious@reddragons.mrs'
        response = self.client.post(self._build_add_url(camp),
                                    data = {'sender':   sender,
                                            'type':     SENDING_TYPE_IMMEDIATE,
                                            'template': template.id,
                                           }
                                   )
        self.assertNoFormError(response)
        self.assertFalse(django_mail.outbox)

        EmailsSendCommand().execute(verbosity=0)

        with self.assertNoException():
            sending = camp.sendings_set.all()[0]

        self.assertEqual(SENDING_STATE_DONE, sending.state)

        messages = django_mail.outbox
        self.assertEqual(len(messages), 3)

        message = messages[0]
        self.assertEqual(template.subject, message.subject)
        self.assertEqual(template.body,    message.body)
        self.assertEqual(sender,           message.from_email)
        self.assertEqual([('', 'text/html')], message.alternatives)
        self.assertFalse(message.attachments)

        self.assertEqual({contact.email, orga1.email, orga2.email},
                         {recipient
                                for message in messages
                                    for recipient in message.recipients()
                         }
                        )

    def test_create04(self):
        "Test deferred"
        user = self.login()
        camp     = EmailCampaign.objects.create(user=user, name='camp01')
        template = EmailTemplate.objects.create(user=user, name='name', subject='subject', body='body')

        #now = datetime.now()
        #sending_date = now.replace(year=now.year + 1)
        now_dt = now()
        sending_date = now_dt + timedelta(weeks=1)
        naive_sending_date = make_naive(sending_date, get_current_timezone())
        data = {'sender':   'vicious@reddragons.mrs',
                'type':     SENDING_TYPE_DEFERRED,
                'template': template.id,
               }

        post = partial(self.client.post, self._build_add_url(camp))
        self.assertNoFormError(post(data=dict(data,
                                              #sending_date=sending_date.strftime('%Y-%m-%d'), #future: OK
                                              #hour=sending_date.hour,
                                              #minute=sending_date.minute,
                                              sending_date=naive_sending_date.strftime('%Y-%m-%d'), #future: OK
                                              hour=naive_sending_date.hour,
                                              minute=naive_sending_date.minute,
                                             )
                                   )
                              )

        with self.assertNoException():
            sending = self.refresh(camp).sendings_set.all()[0]

        self.assertDatetimesAlmostEqual(sending_date, sending.sending_date, seconds=60)

        self.assertFormError(post(data=data), 'form', 'sending_date',
                             _(u"Sending date required for a deferred sending")
                            )

        msg = _(u"Sending date must be is the future")
        self.assertFormError(post(data=dict(data,
                                            sending_date=(now_dt - timedelta(days=1)).strftime('%Y-%m-%d')
                                           )
                                 ),
                             'form', 'sending_date', msg,
                            )
        self.assertFormError(post(data=dict(data,
                                            sending_date=now_dt.strftime('%Y-%m-%d'),
                                           )
                                 ),
                             'form', 'sending_date', msg,
                            )

    def test_create05(self):
        "Test deferred (today)"
        user = self.login()
        camp     = EmailCampaign.objects.create(user=user, name='camp01')
        template = EmailTemplate.objects.create(user=user, name='name', subject='subject', body='body')

        now_dt = now()
        sending_date = now_dt + timedelta(hours=1) # Today if we run the test before 23h...

        naive_sending_date = make_naive(sending_date, get_current_timezone())
        data = {'sender':   'vicious@reddragons.mrs',
                'type':     SENDING_TYPE_DEFERRED,
                'template': template.id,
               }

        post = partial(self.client.post, self._build_add_url(camp))
        self.assertNoFormError(post(data=dict(data,
                                              sending_date=naive_sending_date.strftime('%Y-%m-%d'), # Future: OK
                                              hour=naive_sending_date.hour,
                                              minute=naive_sending_date.minute,
                                             )
                                   )
                              )

        with self.assertNoException():
            sending = self.refresh(camp).sendings_set.all()[0]

        self.assertDatetimesAlmostEqual(sending_date, sending.sending_date, seconds=60)

    def test_inneredit(self):
        user = self.login()
        camp     = EmailCampaign.objects.create(user=user, name='camp01')
        #template = EmailTemplate.objects.create(user=user, name='name', subject='subject', body='body')
        sending  = EmailSending.objects.create(campaign=camp, type=SENDING_TYPE_IMMEDIATE,
                                               sending_date=now(), state=SENDING_STATE_PLANNED,
                                              )

        build_url = self.build_inneredit_url
        self.assertGET(400, build_url(sending, 'campaign'))
        self.assertGET(400, build_url(sending, 'state'))
        self.assertGET(400, build_url(sending, 'subject'))
        self.assertGET(400, build_url(sending, 'body'))
        self.assertGET(400, build_url(sending, 'body_html'))
        self.assertGET(400, build_url(sending, 'signature'))
        self.assertGET(400, build_url(sending, 'attachments'))

        self.assertGET(400, build_url(sending, 'sender'))
        self.assertGET(400, build_url(sending, 'type'))
        self.assertGET(400, build_url(sending, 'sending_date'))
