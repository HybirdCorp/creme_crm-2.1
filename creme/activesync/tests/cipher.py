# -*- coding: utf-8 -*-

try:
    import random

    from creme.creme_core.tests.base import CremeTestCase

    from creme.creme_config.models import SettingValue, SettingKey

    from ..cipher import Cipher
except Exception as e:
    print('Error in <%s>: %s' % (__name__, e))


class CipherTestCase(CremeTestCase):
    def test_cipher01(self):
        text = "Creme is opensrc" # len(text) is explicitly == 16
        ciphertext = Cipher.encrypt(text)
        self.assertEqual(text, Cipher.decrypt(ciphertext))

    def test_cipher02(self):
        text = "Creme" # len(text) is explicitly <= 16
        ciphertext = Cipher.encrypt(text)
        self.assertEqual(text, Cipher.decrypt(ciphertext))

    def test_cipher03(self):
        text = "Creme is a free/open-source" # len(text) is explicitly >= 16 and not mod 16
        ciphertext = Cipher.encrypt(text)
        self.assertEqual(text, Cipher.decrypt(ciphertext))

        text = "".join(str(i) for i in xrange(50))
        ciphertext = Cipher.encrypt(text)
        self.assertEqual(text, Cipher.decrypt(ciphertext))

    def test_cipher04(self):
        for i in xrange(143):
            text = ''.join(chr(random.randint(0, 0xFF)) for i in xrange(i))#Test with text with not always the same length
            ciphertext = Cipher.encrypt(text)
            self.assertEqual(text, Cipher.decrypt(ciphertext))

    def test_cipher05(self):
        for i in xrange(143):
            text = ''.join(chr(random.randint(0, 255)) for i in xrange(i))#Test with text with not always the same length
            ciphertext = Cipher.encrypt(text)
            self.assertEqual(text, Cipher.decrypt(ciphertext))

    def test_cipher_for_db01(self):
        text = "Creme is opensrc"
        ciphertext = Cipher.encrypt_for_db(text)
        self.assertEqual(text, Cipher.decrypt_from_db(ciphertext))

    def test_cipher_for_db02(self):
        for i in xrange(143):
            text = ''.join(chr(random.randint(0, 255)) for i in xrange(i))#Test with text with not always the same length
            ciphertext = Cipher.encrypt_for_db(text)
            self.assertEqual(text, Cipher.decrypt_from_db(ciphertext))

    def test_ciphered_setting_value01(self):
        self.login()
        password = "my password"
        skey_id = 'CipherTestCase-test_ciphered_setting_value01'
        skey = SettingKey.objects.create(id=skey_id, type=SettingKey.STRING)
        sv = SettingValue.objects.get_or_create(key=skey, user=self.user)[0]
        #self.assertEqual(1, SettingValue.objects.count())
        self.assertEqual(1, SettingValue.objects.filter(key=skey).count())

        sv.value = Cipher.encrypt_for_db(password)
        sv.save()

        sv = SettingValue.objects.get(key=skey, user=self.user)
        self.assertEqual(password, Cipher.decrypt_from_db(sv.value))
