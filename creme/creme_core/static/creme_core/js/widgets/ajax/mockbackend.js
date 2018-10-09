/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2018  Hybird

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
*******************************************************************************/

(function($) {
"use strict";

creme.ajax = creme.ajax || {};

creme.ajax.MockAjaxBackend = function(options) {
    this.options = $.extend({
        delay: 500,
        enableUriSearch: false
    }, options || {});

    this.GET =  {};
    this.POST = {};

    this.counts = {GET: 0, POST: 0, SUBMIT: 0};
    this.parser = document.createElement('a');
};

creme.ajax.MockAjaxBackend.prototype = new creme.ajax.Backend();
creme.ajax.MockAjaxBackend.prototype.constructor = creme.ajax.Backend;

$.extend(creme.ajax.MockAjaxBackend.prototype, {
    send: function(url, data, method, on_success, on_error, options) {
        var self = this;
        var method_urls = this[method] || {};
        options = $.extend({}, this.options, options);

        if (options.sync !== true) {
            options.sync = true;
            var delay = isNaN(options.delay) ? 500 : options.delay;

            if (delay > 0) {
                window.setTimeout(function() {
                    self.send(url, data, method, on_success, on_error, options);
                }, delay);

                return;
            }
        }

        if (options.enableUriSearch) {
            var urlInfo = creme.ajax.parseUrl(url);

            if (urlInfo.search) {
                if (method === 'GET') {
                    data = $.extend({}, urlInfo.searchData, data || {});
                } else {
                    data = $.extend({
                        'URI-SEARCH': urlInfo.searchData
                    }, data || {});
                }
            }

            url = urlInfo.pathname.replace(/^\//, '');
        }

        var response = method_urls[url];

        if (response === undefined) {
            console.warn('MockAjaxBackend (404) : ' + method + ' ' + url);
            response = this.response(404, '');
        }

        if (Object.isFunc(response)) {
            try {
                response = creme.object.invoke(response, url, data, options);
            } catch (e) {
                response = this.response(500, '' + e);
            }
        }

        if (options.debug) {
            console.log('mockajax > send > url:', url, 'options:', options, 'response:', response);
        }

        if (response.status !== 200) {
            return creme.object.invoke(on_error, response.responseText, new creme.ajax.AjaxResponse(response.status,
                                                                                                    response.responseText,
                                                                                                    response.xhr));
        }

        return creme.object.invoke(on_success, response.responseText, response.statusText, response);
    },

    get: function(url, data, on_success, on_error, options) {
        this.counts.GET += 1;
        return this.send(url, data, 'GET', on_success, on_error, options);
    },

    post: function(url, data, on_success, on_error, options) {
        this.counts.POST += 1;
        return this.send(url, data, 'POST', on_success, on_error, options);
    },

    submit: function(form, on_success, on_error, options) {
        options = options || {};
        var url = options.action || form.attr('action');
        var data = creme.ajax.serializeFormAsDict(form, options.data);
        this.counts.SUBMIT += 1;
        return this.send(url, data, 'POST', on_success, on_error, options);
    },

    response: function(status, data, header) {
        header = $.extend({
            'content-type': 'text/html'
        }, header || {});

        return new creme.ajax.XHR({
            responseText: data,
            status: status,
            statusText: status !== 200 ? creme.ajax.LOCALIZED_ERROR_MESSAGES[status] : 'ok',
            getResponseHeader: function(name) { return header[name.toLowerCase()]; }
        });
    },

    resetMockCounts: function() {
        this.counts = {GET: 0, POST: 0, SUBMIT: 0};
    }
});
}(jQuery));
