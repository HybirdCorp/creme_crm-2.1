QUnit.module("creme.activities.listview.actions", new QUnitMixin(QUnitEventMixin,
                                                                 QUnitAjaxMixin,
                                                                 QUnitListViewMixin,
                                                                 QUnitDialogMixin, {
}));

QUnit.test('creme.activities.ExportAsICalAction (no selection)', function(assert) {
    var list = this.createListView().controller();
    var action = new creme.activities.ExportAsICalAction(list, {
        url: 'mock/activities/export/ical'
    }).on(this.listviewActionListeners);

    equal(0, list.selectedRowsCount());
    deepEqual([], list.selectedRows());

    this.assertClosedDialog();

    action.start();

    this.assertOpenedAlertDialog(gettext("Please select at least a line in order to export."));
    this.closeDialog();

    deepEqual([['cancel']], this.mockListenerCalls('action-cancel'));
    deepEqual([], this.mockRedirectCalls());
});

QUnit.test('creme.activities.ExportAsICalAction (ok)', function(assert) {
    var list = this.createDefaultListView().controller();
    var action = new creme.activities.ExportAsICalAction(list, {
        url: 'mock/activities/export/ical'
    }).on(this.listviewActionListeners);

    this.setListviewSelection(list, ['1', '2', '3']);

    equal(3, list.selectedRowsCount());
    deepEqual(['1', '2', '3'], list.selectedRows());

    action.start();

    deepEqual([['done']], this.mockListenerCalls('action-done'));
    deepEqual(['/mock/activities/export/ical?id=1&id=2&id=3'], this.mockRedirectCalls());
});

/*
QUnit.test('creme.activities.exportAsICal', function(assert) {
    var list = this.createDefaultListView().controller();

    $(list).find('#selected_rows').val('1,2,3');
    equal(3, list.selectedRowsCount());
    deepEqual(['1', '2', '3'], list.selectedRows());

    deepEqual([], this.mockRedirectCalls());

    creme.activities.exportAsICal(list, 'mock/activities/export/ical');

    deepEqual(['/mock/activities/export/ical?id=1&id=2&id=3'], this.mockRedirectCalls());
});
*/
