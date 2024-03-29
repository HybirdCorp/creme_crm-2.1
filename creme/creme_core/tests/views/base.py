# -*- coding: utf-8 -*-

try:
    from tempfile import NamedTemporaryFile
    from unittest import skipIf

    # import html5lib
    from bleach._vendor import html5lib  # Avoid a dependence only for test

    from django.contrib.contenttypes.models import ContentType
    from django.urls import reverse

    from ..base import CremeTestCase
    from creme.creme_core.auth.entity_credentials import EntityCredentials
    from creme.creme_core.creme_jobs.mass_import import mass_import_type
    from creme.creme_core.models import SetCredentials, MassImportJobResult

    from creme.documents.models import Document, Folder, FolderCategory
except Exception as e:
    print('Error in <{}>: {}'.format(__name__, e))

try:
    from creme.creme_core.utils.xlwt_utils import XlwtWriter
    from creme.creme_core.backends import import_backend_registry

    no_XLS_lib = 'xls' not in import_backend_registry.extensions
except:
    no_XLS_lib = True


def skipIfNoXLSLib(test_func):
    return skipIf(no_XLS_lib, "Skip tests, couldn't find xlwt or xlrd libs")(test_func)


class ViewsTestCase(CremeTestCase):
    def login(self, is_superuser=True, *args, **kwargs):
        user = super().login(is_superuser, *args, **kwargs)

        SetCredentials.objects.create(role=self.role,
                                      value=EntityCredentials.VIEW   |
                                            EntityCredentials.CHANGE |
                                            EntityCredentials.DELETE |
                                            EntityCredentials.LINK   |
                                            EntityCredentials.UNLINK,
                                      set_type=SetCredentials.ESET_OWN,
                                     )

        return user

    def _set_all_creds_except_one(self, excluded):  # TODO: in CremeTestCase ?
        value = EntityCredentials.NONE

        for cred in (EntityCredentials.VIEW, EntityCredentials.CHANGE,
                     EntityCredentials.DELETE, EntityCredentials.LINK,
                     EntityCredentials.UNLINK):
            if cred != excluded:
                value |= cred

        SetCredentials.objects.create(role=self.user.role, value=value,
                                      set_type=SetCredentials.ESET_ALL,
                                     )


class BrickTestCaseMixin:
    def get_html_tree(self, content):
        return html5lib.parse(content, namespaceHTMLElements=False)

    def get_brick_node(self, tree, brick_id):
        brick_node = tree.find(".//div[@id='{}']".format(brick_id))
        self.assertIsNotNone(brick_node, 'The brick id="{}" is not found.'.format(brick_id))

        classes = brick_node.attrib.get('class')
        self.assertIsNotNone(classes, 'The brick id="{}" is not a valid brick (no "class" attribute).'.format(brick_id))
        self.assertIn('brick', classes.split(), 'The brick id="{}" is not a valid brick (no "brick" class).'.format(brick_id))

        return brick_node

    def assertNoBrick(self, tree, brick_id):
        self.assertIsNone(tree.find(".//div[@id='{}']".format(brick_id)),
                          'The brick id="{}" has been unexpectedly found.'.format(brick_id)
                         )

    def assertInstanceLink(self, brick_node, entity):
        link_node = brick_node.find(".//a[@href='{}']".format(entity.get_absolute_url()))
        self.assertIsNotNone(link_node)
        self.assertEqual(str(entity), link_node.text)

    def assertNoInstanceLink(self, brick_node, entity):
        self.assertIsNone(brick_node.find(".//a[@href='{}']".format(entity.get_absolute_url())))

    def assertBrickHasClass(self, brick_node, css_class):
        self.assertIn(css_class, brick_node.attrib.get('class').split())

    def assertBrickHasNotClass(self, brick_node, css_class):
        self.assertNotIn(css_class, brick_node.attrib.get('class').split())

    def get_brick_tile(self, content_node, key):
        tile_node = content_node.find('.//div[@data-key="%s"]' % key)
        self.assertIsNotNone(tile_node)

        value_node = tile_node.find('.//span[@class="brick-tile-value"]')
        self.assertIsNotNone(value_node)

        return value_node

    def get_brick_title(self, brick_node):
        span_node = brick_node.find('.//span[@class="brick-title"]')
        self.assertIsNotNone(span_node)

        return span_node.text.strip()

    def get_brick_header_buttons(self, brick_node):
        buttons_node = brick_node.find('.//div[@class="brick-header-buttons"]')
        self.assertIsNotNone(buttons_node)

        return buttons_node

    def assertBrickHeaderHasButton(self, buttons_node, url, label):
        button_node = buttons_node.find(f'.//a[@href="{url}"]')
        if button_node is None:
            self.fail(
                'The <a> markup with href="{url}" has not been found '
                '(URLs found: {found}).'.format(
                    url=url,
                    found=', '.join(
                        '"{}"'.format(a.attrib.get('href'))
                        for a in buttons_node.findall('.//a')
                    ),
                )
            )

        button_label = button_node.attrib.get('title')  # TODO: get the inner-span instead ?
        if label != button_label:
            self.fail(
                f'The button has been found but with a different label:\n'
                f'Expected: {label}\n'
                f'Found: {button_label}'
            )

    def assertBrickHeaderHasNoButton(self, buttons_node, url):
        button_node = buttons_node.find(f'.//a[@href="{url}"]')
        if button_node is not None:
            self.fail(f'The <a> markup with href="{url}" has been unexpectedly found.')


# class CSVImportBaseTestCaseMixin:
class MassImportBaseTestCaseMixin:
    def _assertNoResultError(self, results):
        for r in results:
            if r.messages:
                self.fail('Import error: {}'.format(r.messages))

    def _build_file(self, content, extension=None):
        tmpfile = NamedTemporaryFile(suffix=".%s" % extension if extension else '')
        tmpfile.write(content)
        tmpfile.flush()

        return tmpfile

    def _build_doc(self, tmpfile):
        tmpfile.file.seek(0)
        category = FolderCategory.objects.create(id=10, name='Test category')
        folder = Folder.objects.create(user=self.user, title='Test folder',
                                       parent_folder=None,
                                       category=category,
                                      )

        title = 'Test doc'
        response = self.client.post(reverse('documents__create_document'), follow=True,
                                    data={'user':        self.user.id,
                                          'title':       title,
                                          'description': 'CSV file for contacts',
                                          'filedata':    tmpfile,
                                          'linked_folder': folder.id,
                                         },
                                   )
        self.assertNoFormError(response)

        with self.assertNoException():
            doc = Document.objects.get(title=title)

        return doc

    def _build_csv_doc(self, lines, separator=',', extension='csv'):
        content = '\n'.join(separator.join('"{}"'.format(item) for item in line) for line in lines)
        tmpfile = self._build_file(content.encode(), extension)

        return self._build_doc(tmpfile)

    def _build_xls_doc(self, lines, extension='xls'):
        tmpfile = self._build_file(b'', extension)
        wb = XlwtWriter()
        for line in lines:
            wb.writerow(line)
        wb.save(tmpfile.name)

        return self._build_doc(tmpfile)

    def _build_import_url(self, model):
        ct = ContentType.objects.get_for_model(model)
        return reverse('creme_core__mass_import', args=(ct.id,))

    def _get_job(self, response):
        with self.assertNoException():
            return response.context['job']

    def _get_job_results(self, job):
        return MassImportJobResult.objects.filter(job=job)

    def _execute_job(self, response):
        job = self._get_job(response)
        mass_import_type.execute(job)

        return job
