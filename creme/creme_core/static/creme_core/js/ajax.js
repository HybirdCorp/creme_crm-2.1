/*
 * Requires : jQuery
 *            creme.utils.js
 */

/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2014  Hybird

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

//Code from Django doc: http://docs.djangoproject.com/en/1.2/ref/contrib/csrf/#csrf-ajax
$('html').ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

//Traditional parameter serialization (true: a=1&a=2&b=3, false: a[]=1&a[]=2&b=3)
//So, with false if a param is used more than once "[]" is appended to the param name
jQuery.ajaxSettings.traditional = true;

creme.ajax = {}

creme.ajax.submit = function(form, data, options) {//Tip: If data === true => data are taken from the form
        var $form = $(form);

        var defaults = {
            method: $form.attr('method'),
            action: ($form.attr('action') == "") ? window.location.href : $form.attr('action'),
            async: true,
            cache: true,
            beforeSend: null,
            success: null,
            beforeError: null,
            beforeComplete: null,
            error: function() {
                creme.utils.showErrorNReload();
            },
            afterError: null,
            complete: null
        };

        var opts = $.extend(defaults, options);
        if (data === true) {
            data = $form.serialize();
        }

        $.ajax({
              url: opts.action,
              type: opts.method,
              data: data,
              async: opts.async,
              beforeSend: function(request){
                  creme.utils.loading('loading', false, {});
                  if(opts.beforeSend) opts.beforeSend(request);
              },
              success: function(returnedData, status) {
                if (opts.success) opts.success(returnedData, status);
              },
              error: function(request, status, error) {
                  if (opts.beforeError) opts.beforeError(request, status, error);
                  if (opts.error) opts.error(request, status, error);
                  if (opts.afterError) opts.afterError(request, status, error);
              },
              complete: function(request, status) {
                  if (opts.beforeComplete) opts.beforeComplete(request, status);
                  creme.utils.loading('loading', true, {});
                  if (opts.complete) opts.complete(request, status);
              }
        });
};

creme.ajax.ajax = function(options) {
        options = $.extend({
            type: "GET",
            url: "",
            async: true,
            data: {},
            dataType: "html",
            cache: true,
            beforeSend: null,
            success: null,
            beforeError: null,
            beforeComplete: null,
            error: function() {
                creme.utils.showErrorNReload();
            },
            afterError: null,
            complete: null
        }, options);

        $.ajax({
              url: options.url,
              type: options.type,
              data: options.data,
              async: options.async,
              dataType: options.dataType,
              beforeSend: function(request) {
                  creme.utils.loading('loading', false, {});
                  if (options.beforeSend && $.isFunction(options.beforeSend)) options.beforeSend(request);
              },
              success: function(returnedData, status) {
                if (options.success && $.isFunction(options.success)) options.success(returnedData, status);
              },
              error: function(request, status, error) {
                  if (options.beforeError && $.isFunction(options.beforeError)) options.beforeError(request, status, error);
                  if (options.error && $.isFunction(options.error)) options.error(request, status, error);
                  if (options.afterError && $.isFunction(options.afterError)) options.afterError(request, status, error);
              },
              complete: function (request, status) {
                  if (options.beforeComplete) options.beforeComplete(request, status);
                  creme.utils.loading('loading', true, {});
                  if (options.complete) options.complete(request, status);
              }
        });
};

creme.ajax.get = function(options) {
    creme.ajax.ajax($.extend({type:"GET"}, options));
};

creme.ajax.post = function(options) {
    creme.ajax.ajax($.extend({type:"POST"}, options));
};

creme.ajax.reloadContent = function($target, target_url) {
    creme.ajax.get({
        url: target_url,
        success: function(data) {
            $target.empty().html(data);
        }
    });
};

/*
 * creme.ajax.iframeSubmit($('#myform'), function(data) {
             console.log(data) // result html content (body of iframe)
      });
 */
/*
creme.ajax.iframeSubmit = function(form, success_cb, pop_options) {
    var delay = 1;
    var id = new Date().getTime()
    var iframe = $('<iframe style="position:absolute;top:-1000px;left:-1000px;"><html><head></head><body></body></html></iframe>').attr('id', id).appendTo($('body'))

    setTimeout(function() {
        var submit = creme.ajax.iframePopulate(iframe, form, pop_options);
        submit.trigger('click');

        iframe.load(function() {
            success_cb($(this).contents().find('body').html());
            iframe.remove();
        });
    }, delay);
};
*/

/*
creme.ajax.iframePopulate = function(iframe, form, options) {
    var iform = $('<form>').attr('action', options['action']||form.attr('action'))
                           .attr('method', 'post')
                           .attr('enctype', form.attr('enctype'));

    $('input, textarea', form).each(function() {
        iform.append($(this).clone().text($(this).val()));
    });

    $('select', form).each(function() {
        iform.append($(this).clone().val($(this).val()).change());
    });

        $('[name=whoami]').each(function(){
            iform.append($(this).clone().text($(this).val()));
        });

    iframe.contents().find('body').append(iform);

    return $('<input type="submit" name="submit" value="1" id="submit"/>').appendTo(iform);
};
*/

/*
creme.ajax.iframeSubmit = function(form, success_cb, error_cb, options) {
    var delay = 100;
    
    // build iframe with unique id
    var id = new Date().getTime();
    var iframe = $('<iframe src="javascript:false;" style="display:none;"><html><head></head><body></body></html></iframe>');
    iframe.attr('id', id).attr('name', id).appendTo($('body'));

    // specific iframe for IE
    if ($.browser.msie) {
        iframe.attr('src', "javascript:'<html></html>';").attr('target', '_blank');
    }

    // add custom action if needed
    var form_action = form.attr('action');
    form.attr('action', (options['action'] !== undefined ? options['action'] : form_action));

    // iframe response callback
    var iframe_success_cb = function(event) {
        if ($.browser.msie) {
            success_cb(iframe.contents().find('body').clone(true).html(), event);
        } else {
            success_cb(iframe.contents().find('body').html(), event);
        }

        form.attr('action', form_action);
        iframe.remove();
    };

    // iframe error callback
    var iframe_error_cb = function(event) {
        iframe.unbind('error', iframe_error_cb);

        error_cb(event);
        form.attr('action', form_action);
        iframe.remove();
    };

    window.setTimeout(function() {
        iframe.bind('load', iframe_success_cb);
        iframe.bind('error', iframe_success_cb);

        var submit = creme.ajax.iframeRedirect(iframe, form);
        submit.trigger('click');

    }, delay);
};

creme.ajax.iframeRedirect = function(iframe, form) {
    var iform = form.attr('target', iframe.attr('name'));
    return $('<input type="submit" name="submit" value="1" id="submit" style="display:none"/>').appendTo(iform);
};
*/

creme.ajax.json = {};
creme.ajax.json._handleSendError = function(req, textStatus, errorThrown) {
    switch(textStatus) {
        case "parsererror":
            return {type: "request", status: req.status, message: "JSON parse error", request: req}
            break;
        default:
            return {type: "request", status: req.status, message: "" + req.status + " " + req.statusText, request: req}
    }
};

creme.ajax.json.send = function(url, data, success_cb, error_cb, sync, method, parameters) {
    var ajax_parameters = {
        async: !sync,
        type: method,
        url: url,
        data: data !== undefined ? data : '',
        dataType: "json",
        success: function(data, textStatus) {
            if (success_cb !== undefined) {
                success_cb(data, textStatus);
            }
        },
        error: function(req, textStatus, errorThrown) {
            if (error_cb !== undefined) {
                error_cb(req.responseText, creme.ajax.json._handleSendError(req, textStatus, errorThrown));
            }
        }
    };

    if (parameters != undefined) {
        ajax_parameters = $.extend(ajax_parameters, parameters);
    }

    $.ajax(ajax_parameters);
};

creme.ajax.json.post = function(url, data, success_cb, error_cb, sync, parameters) {
    creme.ajax.json.send(url, data, success_cb, error_cb, sync, "POST", parameters);
};

creme.ajax.json.get = function(url, data, success_cb, error_cb, sync, parameters) {
    creme.ajax.json.send(url, data, success_cb, error_cb, sync, "GET", parameters);
};

creme.ajax.json.isvalid = function(data) {
    return typeof data === 'string' &&
           /^[\],:{}\s]*$/.test(data.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, "@")
                                    .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]")
                                    .replace(/(?:^|:|,)(?:\s*\[)+/g, ""));
}

// Code copied from JQuery 1.4.*
creme.ajax.json.parse = function(data) {
    if (typeof data !== "string" || !data) {
        return null;
    }

    // Make sure leading/trailing whitespace is removed (IE can't handle it)
    data = jQuery.trim( data );

    // Make sure the incoming data is actual JSON
    // Logic borrowed from http://json.org/json2.js
    if (/^[\],:{}\s]*$/.test(data.replace(/\\(?:["\\\/bfnrt]|u[0-9a-fA-F]{4})/g, "@")
        .replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g, "]")
        .replace(/(?:^|:|,)(?:\s*\[)+/g, ""))) {

        try {
            // Try to use the native JSON parser first
            return window.JSON && window.JSON.parse ?
                window.JSON.parse(data) :
                (new Function("return " + data))();
        } catch(err) {
            //console.log("Invalid JSON: " + data);
            return null;
        }

    } else {
        //console.log( "Invalid JSON: " + data );
        return null;
    }
};

creme.ajax.json.ajaxFormSubmit = function($form, success_cb, error_cb, sync, parameters) {
    creme.ajax.json.post($form.attr('action'),
                         $form.serialize(),
                         success_cb || function(data) {$form.html(data.form);},
                         error_cb, sync, parameters
    );
}
