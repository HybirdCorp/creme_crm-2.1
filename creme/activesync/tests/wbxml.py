# -*- coding: utf-8 -*-

try:
    from StringIO import StringIO
    from os.path import join, dirname, abspath
    from xml.etree.ElementTree import XML, tostring
    from xml.parsers import expat

    from django.core.files import File

    from creme_core.tests.base import CremeTestCase

    from activesync.wbxml.dtd import AirsyncDTD_Reverse, AirsyncDTD_Forward
    from activesync.wbxml.codec import WBXMLEncoder, WBXMLDecoder, WrongXMLType
except Exception as e:
    print 'Error:', e


DEFAULT_CHUNK_SIZE = File.DEFAULT_CHUNK_SIZE

class ActiveSyncWbxmlTestCase(CremeTestCase):
    def setUp(self):
        self.decoder = WBXMLDecoder(AirsyncDTD_Forward)
        self.encoder = WBXMLEncoder(AirsyncDTD_Reverse)
        self.xml_path = join(dirname(abspath(__file__)), 'data')
        self.files = [("test_%s.xml" % i, "test_%s.wbxml" % i) for i in xrange(1, 7)]

    def _open_n_read(self, filename, mode='r'):
        path = join(self.xml_path, filename)
        content = StringIO()

        with open(path, mode) as f:
            for ch in f.read(DEFAULT_CHUNK_SIZE):
                content.write(ch)

        return_content = content.getvalue()

        content.close()

        return return_content

    def test_encoder01(self):
        xml_str1 = '<?xml version="1.0" encoding="UTF-8"?><FolderSync xmlns="FolderHierarchy:"><SyncKey>0</SyncKey></FolderSync>'
        encoder = WBXMLEncoder(AirsyncDTD_Reverse)
        encoded = encoder.encode(xml_str1)
        self.assertEqual(encoded, '\x03\x01j\x00\x00\x07VR\x030\x00\x01\x01')

        self.assertEqual(encoder.get_ns('{FolderHierarchy:}FolderSync'), 'FolderHierarchy:')
        self.assertIsNone(encoder.get_ns('FolderHierarchy:FolderSync'))

        self.assertEqual(encoder.get_tag('{FolderHierarchy:}FolderSync', 'FolderHierarchy:'), 'FolderSync')
        self.assertEqual(encoder.get_tag('{FolderHierarchy:}FolderSync', None), '{FolderHierarchy:}FolderSync')

    def test_encoder02(self):
        xml_str2 = """<?xml version="1.0"?><FolderSync xmlns="FolderHierarchy:"><Status xmlns="FolderHierarchy:">1</Status><SyncKey xmlns="FolderHierarchy:">{112ef5a8-47fb-44ca-94e2-d0770e6d7c6b}1</SyncKey><Changes xmlns="FolderHierarchy:"><Count xmlns="FolderHierarchy:">12</Count><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310d00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Inbox</DisplayName><Type xmlns="FolderHierarchy:">2</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310e00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Outbox</DisplayName><Type xmlns="FolderHierarchy:">6</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310f00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Deleted Items</DisplayName><Type xmlns="FolderHierarchy:">4</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311000000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Sent Items</DisplayName><Type xmlns="FolderHierarchy:">5</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311100000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Contacts</DisplayName><Type xmlns="FolderHierarchy:">9</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311200000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Calendar</DisplayName><Type xmlns="FolderHierarchy:">8</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311300000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Drafts</DisplayName><Type xmlns="FolderHierarchy:">3</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311400000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Journal</DisplayName><Type xmlns="FolderHierarchy:">11</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311500000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Notes</DisplayName><Type xmlns="FolderHierarchy:">10</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311600000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Tasks</DisplayName><Type xmlns="FolderHierarchy:">7</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311700000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Junk E-mail</DisplayName><Type xmlns="FolderHierarchy:">12</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311b00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">RSS Feeds</DisplayName><Type xmlns="FolderHierarchy:">1</Type></Add></Changes></FolderSync>"""
        xml2 = XML(xml_str2)
        wbxml2   = '\x03\x01j\x00\x00\x07VL\x031\x00\x01R\x03{112ef5a8-47fb-44ca-94e2-d0770e6d7c6b}1\x00\x01NW\x0312\x00\x01OH\x032e9ce20a99cc4bc39804d5ee956855310d00000000000000\x00\x01I\x030\x00\x01G\x03Inbox\x00\x01J\x032\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855310e00000000000000\x00\x01I\x030\x00\x01G\x03Outbox\x00\x01J\x036\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855310f00000000000000\x00\x01I\x030\x00\x01G\x03Deleted Items\x00\x01J\x034\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311000000000000000\x00\x01I\x030\x00\x01G\x03Sent Items\x00\x01J\x035\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311100000000000000\x00\x01I\x030\x00\x01G\x03Contacts\x00\x01J\x039\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311200000000000000\x00\x01I\x030\x00\x01G\x03Calendar\x00\x01J\x038\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311300000000000000\x00\x01I\x030\x00\x01G\x03Drafts\x00\x01J\x033\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311400000000000000\x00\x01I\x030\x00\x01G\x03Journal\x00\x01J\x0311\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311500000000000000\x00\x01I\x030\x00\x01G\x03Notes\x00\x01J\x0310\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311600000000000000\x00\x01I\x030\x00\x01G\x03Tasks\x00\x01J\x037\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311700000000000000\x00\x01I\x030\x00\x01G\x03Junk E-mail\x00\x01J\x0312\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311b00000000000000\x00\x01I\x030\x00\x01G\x03RSS Feeds\x00\x01J\x031\x00\x01\x01\x01\x01'
        encoded2 = WBXMLEncoder(AirsyncDTD_Reverse).encode(xml2)
        self.assertEqual(encoded2, wbxml2)

    def test_encoder03(self):
        xml_str3 = """<?xml version="1.0" encoding="utf-8"?><Sync xmlns="AirSync:" xmlns:A1="Contacts:"><Collections><Collection><SyncKey>0</SyncKey><CollectionId>2e9ce20a99cc4bc39804d5ee956855311500000000000000</CollectionId><Supported><A1:JobTitle/><A1:Department/></Supported></Collection></Collections></Sync>"""
        xml3     = XML(xml_str3)
        wbxml3   = '\x03\x01j\x00E\\OK\x030\x00\x01R\x032e9ce20a99cc4bc39804d5ee956855311500000000000000\x00\x01`\x00\x01(\x1a\x01\x01\x01\x01'
        encoded3 = WBXMLEncoder(AirsyncDTD_Reverse).encode(xml3)
        self.assertEqual(encoded3, wbxml3)

    def test_encoder04(self):
        xml_str4 = """<?xml version="1.0" encoding="utf-8"?><Sync xmlns="AirSync:" xmlns:A1="Contacts:"><Collections><Collection><Class>Contacts</Class><SyncKey>0</SyncKey><CollectionId>2e9ce20a99cc4bc39804d5ee956855311b00000000000000</CollectionId><DeletesAsMoves/><GetChanges/></Collection></Collections></Sync>"""
        xml4     = XML(xml_str4)
        wbxml4 = '\x03\x01j\x00E\\OP\x03Contacts\x00\x01K\x030\x00\x01R\x032e9ce20a99cc4bc39804d5ee956855311b00000000000000\x00\x01\x1e\x13\x01\x01\x01'
        encoded4 = WBXMLEncoder(AirsyncDTD_Reverse).encode(xml4)
        self.assertEqual(encoded4, wbxml4)

    def test_encoder_ns_settings(self):
        xml_str = """<?xml version="1.0" encoding="utf-8"?><Settings xmlns="Settings:"><DeviceInformation><Set><Model>CremePhone</Model><IMEI>1234567890</IMEI><FriendlyName>Creme CRM Phone</FriendlyName><OS>Creme/django</OS><OSLanguage>python</OSLanguage><PhoneNumber>0000000000</PhoneNumber><MobileOperator>Hybird</MobileOperator><UserAgent>CremeCRM/1.0</UserAgent></Set></DeviceInformation></Settings>"""
        xml     = XML(xml_str)
        wbxml   = '\x03\x01j\x00\x00\x12EVHW\x03CremePhone\x00\x01X\x031234567890\x00\x01Y\x03Creme CRM Phone\x00\x01Z\x03Creme/django\x00\x01[\x03python\x00\x01\\\x030000000000\x00\x01b\x03Hybird\x00\x01`\x03CremeCRM/1.0\x00\x01\x01\x01\x01'
        encoded = WBXMLEncoder(AirsyncDTD_Reverse).encode(xml)
        self.assertEqual(encoded, wbxml)

    def test_encoder05(self):
        self.assertRaises(WrongXMLType, WBXMLEncoder(AirsyncDTD_Reverse).encode, None)
        self.assertRaises(expat.ExpatError, WBXMLEncoder(AirsyncDTD_Reverse).encode, '')

    def test_encoder06(self):
        xml_str   = self._open_n_read('test_6.xml')
        xml       = XML(xml_str)
        wbxml_str = self._open_n_read('test_6.wbxml')
        encoded   = WBXMLEncoder(AirsyncDTD_Reverse).encode(xml)
        self.assertEqual(encoded, wbxml_str)

    def test_encoder07(self):
        for xml_file, wbxml_file in self.files:
            #print "Testing with files (%s, %s)" % (xml_file, wbxml_file)
            xml_str   = self._open_n_read(xml_file)
            wbxml_str = self._open_n_read(wbxml_file)

            xml       = XML(xml_str)

            encoder   = WBXMLEncoder(AirsyncDTD_Reverse)
            encoded   = encoder.encode(xml)
            self.assertEqual(encoded, wbxml_str)
            self.assertEqual(encoder.encode(xml), wbxml_str)

    ################ Decoder tests #################
    def test_decoder01(self):
        wbxml_str = '\x03\x01j\x00\x00\x07VR\x030\x00\x01\x01'
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = '<?xml version="1.0" encoding="UTF-8"?><FolderSync xmlns="FolderHierarchy:"><SyncKey>0</SyncKey></FolderSync>'
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder02(self):
        wbxml_str = '\x03\x01j\x00\x00\x07VL\x031\x00\x01R\x03{112ef5a8-47fb-44ca-94e2-d0770e6d7c6b}1\x00\x01NW\x0312\x00\x01OH\x032e9ce20a99cc4bc39804d5ee956855310d00000000000000\x00\x01I\x030\x00\x01G\x03Inbox\x00\x01J\x032\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855310e00000000000000\x00\x01I\x030\x00\x01G\x03Outbox\x00\x01J\x036\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855310f00000000000000\x00\x01I\x030\x00\x01G\x03Deleted Items\x00\x01J\x034\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311000000000000000\x00\x01I\x030\x00\x01G\x03Sent Items\x00\x01J\x035\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311100000000000000\x00\x01I\x030\x00\x01G\x03Contacts\x00\x01J\x039\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311200000000000000\x00\x01I\x030\x00\x01G\x03Calendar\x00\x01J\x038\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311300000000000000\x00\x01I\x030\x00\x01G\x03Drafts\x00\x01J\x033\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311400000000000000\x00\x01I\x030\x00\x01G\x03Journal\x00\x01J\x0311\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311500000000000000\x00\x01I\x030\x00\x01G\x03Notes\x00\x01J\x0310\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311600000000000000\x00\x01I\x030\x00\x01G\x03Tasks\x00\x01J\x037\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311700000000000000\x00\x01I\x030\x00\x01G\x03Junk E-mail\x00\x01J\x0312\x00\x01\x01OH\x032e9ce20a99cc4bc39804d5ee956855311b00000000000000\x00\x01I\x030\x00\x01G\x03RSS Feeds\x00\x01J\x031\x00\x01\x01\x01\x01'
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = """<?xml version="1.0"?><FolderSync xmlns="FolderHierarchy:"><Status xmlns="FolderHierarchy:">1</Status><SyncKey xmlns="FolderHierarchy:">{112ef5a8-47fb-44ca-94e2-d0770e6d7c6b}1</SyncKey><Changes xmlns="FolderHierarchy:"><Count xmlns="FolderHierarchy:">12</Count><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310d00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Inbox</DisplayName><Type xmlns="FolderHierarchy:">2</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310e00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Outbox</DisplayName><Type xmlns="FolderHierarchy:">6</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855310f00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Deleted Items</DisplayName><Type xmlns="FolderHierarchy:">4</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311000000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Sent Items</DisplayName><Type xmlns="FolderHierarchy:">5</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311100000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Contacts</DisplayName><Type xmlns="FolderHierarchy:">9</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311200000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Calendar</DisplayName><Type xmlns="FolderHierarchy:">8</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311300000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Drafts</DisplayName><Type xmlns="FolderHierarchy:">3</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311400000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Journal</DisplayName><Type xmlns="FolderHierarchy:">11</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311500000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Notes</DisplayName><Type xmlns="FolderHierarchy:">10</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311600000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Tasks</DisplayName><Type xmlns="FolderHierarchy:">7</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311700000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">Junk E-mail</DisplayName><Type xmlns="FolderHierarchy:">12</Type></Add><Add xmlns="FolderHierarchy:"><ServerId xmlns="FolderHierarchy:">2e9ce20a99cc4bc39804d5ee956855311b00000000000000</ServerId><ParentId xmlns="FolderHierarchy:">0</ParentId><DisplayName xmlns="FolderHierarchy:">RSS Feeds</DisplayName><Type xmlns="FolderHierarchy:">1</Type></Add></Changes></FolderSync>"""
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder03(self):
        wbxml_str = '\x03\x01j\x00E\\OK\x030\x00\x01R\x032e9ce20a99cc4bc39804d5ee956855311500000000000000\x00\x01`\x00\x01(\x1a\x01\x01\x01\x01'
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = """<?xml version="1.0" encoding="utf-8"?><Sync xmlns="AirSync:" xmlns:A1="Contacts:"><Collections><Collection><SyncKey>0</SyncKey><CollectionId>2e9ce20a99cc4bc39804d5ee956855311500000000000000</CollectionId><Supported><A1:JobTitle/><A1:Department/></Supported></Collection></Collections></Sync>"""
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder04(self):
        wbxml_str = '\x03\x01j\x00E\\OP\x03Contacts\x00\x01K\x030\x00\x01R\x032e9ce20a99cc4bc39804d5ee956855311b00000000000000\x00\x01\x1e\x13\x01\x01\x01'
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = """<?xml version="1.0" encoding="utf-8"?><Sync xmlns="AirSync:" xmlns:A1="Contacts:"><Collections><Collection><Class>Contacts</Class><SyncKey>0</SyncKey><CollectionId>2e9ce20a99cc4bc39804d5ee956855311b00000000000000</CollectionId><DeletesAsMoves/><GetChanges/></Collection></Collections></Sync>"""
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder05(self):
        wbxml_str = '\x03\x01j\x00E\\OP\x03Contacts\x00\x01K\x031303376515199\x00\x01R\x03Contact:DEFAULT\x00\x01VGL\x032\x00\x01]\x00\x01i\x03Creme\x00\x01_\x03Fulbert\x00\x01^\x03Monsieur Fulbert Creme\x00\x01v\x03Monsieur\x00\x01\x01\x01\x01\x01\x01\x01'
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = """<?xml version="1.0" encoding="utf-8"?><Sync xmlns="AirSync:" xmlns:A1="Contacts:" xmlns:A3="Contacts2:" xmlns:A2="AirSyncBase:"><Collections><Collection><Class>Contacts</Class><SyncKey>1303376515199</SyncKey><CollectionId>Contact:DEFAULT</CollectionId><Commands><Add><ClientId>2</ClientId><ApplicationData><A1:LastName>Creme</A1:LastName><A1:FirstName>Fulbert</A1:FirstName><A1:FileAs>Monsieur Fulbert Creme</A1:FileAs><A1:Title>Monsieur</A1:Title></ApplicationData></Add></Commands></Collection></Collections></Sync>"""
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder06(self):
#        wbxml_str = '\x03\x01j\x00E\\OP\x03Contacts\x00\x01K\x031303376516361\x00\x01R\x03Contact:DEFAULT\x00\x01VHM\x033830364049385079147\x00\x01]\x00\x01i\x03Bros\x00\x01h\x03Plombier\x00\x01_\x03Mario\x00\x01|\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\x00\x01[\x03mario@bros.com\x00\x01Y\x03Nintendo\x00\x01v\x03Monsieur\x00\x01^\x03Monsieur Mario Bros\x00\x01\x01\x01\x01\x01\x01\x01'
        wbxml_str = self._open_n_read('test_6.wbxml')
        decoded   = self.decoder.decode(wbxml_str)
        xml_str   = self._open_n_read('test_6.xml')
        self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    def test_decoder07(self):
        decoder = self.decoder

        for xml, wbxml in self.files:
            #print "Testing with files (%s, %s)" % (xml, wbxml)
            wbxml_str = self._open_n_read(wbxml)

            decoded   = decoder.decode(wbxml_str)
            xml_str   = self._open_n_read(xml)
            self.assertEqual(tostring(decoded), tostring(XML(xml_str)))

    ################ Encoder - decoder test ################
    def test_encoder_decoder01(self):
        xml_str = self._open_n_read('test_6.xml')
        xml     = XML(xml_str)#ElementTree instance

        encoded = self.encoder.encode(xml_str)
        decoded = self.decoder.decode(encoded)
        self.assertEqual(tostring(decoded), tostring(xml))

    def test_encoder_decoder02(self):
        xml_str = self._open_n_read('test_1.xml')
        xml     = XML(xml_str)#ElementTree instance

        encoded = self.encoder.encode(xml_str)
        decoded = self.decoder.decode(encoded)
        self.assertEqual(tostring(decoded), tostring(xml))

    def test_encoder_decoder03(self):
        for xml_file, wbxml_file in self.files:
            xml_str = self._open_n_read(xml_file)
            xml     = XML(xml_str)#ElementTree instance

            encoded = self.encoder.encode(xml_str)
            decoded = self.decoder.decode(encoded)
            self.assertEqual(tostring(decoded), tostring(xml))

    def test_decoder_encoder01(self):
        for xml_file, wbxml_file in self.files:
            wbxml_str = self._open_n_read(wbxml_file)

            decoded = self.decoder.decode(wbxml_str)
            encoded = self.encoder.encode(decoded)
            self.assertEqual(encoded, wbxml_str)
