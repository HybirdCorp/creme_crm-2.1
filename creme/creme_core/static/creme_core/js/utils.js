/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2015  Hybird

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

creme.utils = {};

creme.utils.openWindow = function (url, name, params) {
    window[name] = window.open(url, name, params || 'menubar=no, status=no, scrollbars=yes, menubar=no, width=800, height=600');
}

creme.utils.reload = function (target) {
    var target = target || window;
    target.location.href = target.location.href;
}

creme.utils.goTo = function(url, target) {
    var target = target || window;
    target.location.href = url;
}

creme.utils.showPageLoadOverlay = function() {
    //console.log('show loading overlay');
    creme.utils.loading('', false);
} 

creme.utils.hidePageLoadOverlay = function() {
    //console.log('hide loading overlay');
    creme.utils.loading('', true);
} 

creme.utils.loading = function(div_id, is_loaded, params) {
    var overlay = creme.utils._overlay;

    if (overlay === undefined) {
        overlay = creme.utils._overlay = new creme.dialog.Overlay();
        overlay.bind($('body'))
               .addClass('page-loading')
               .content($('<h2>').append($('<img>').attr('src', creme_media_url("images/wait.gif")),
                                         $('<span>').text(gettext('Loading...'))));

        overlay._loadstack = 0;
    }

    overlay._loadstack += !is_loaded ? 1 : -1;

    var visible = overlay._loadstack > 0;
    overlay.update(visible, null, visible ? 100 : 0);
}

// TODO : deprecated, only used by creme.utils.showInnerPopup.
creme.utils.showDialog = function(text, options, div_id) {
    var $div = $('#' + div_id);

    if ($div.size() == 0) {
        var d = new Date();
        div_id = d.getTime().toString() + Math.ceil(Math.random() * 1000000);
        $div = $('<div id="' + div_id + '"  style="display:none;"></div>');
        $(document.body).append($div);
    }
    $div.html(text);

    $div.dialog(jQuery.extend({
        buttons: [{text: gettext("Ok"),
                   click: function() {
                            $(this).dialog("close");
                   }
                 }
        ],
        closeOnEscape: false,
        /*hide: 'slide',
        show: 'slide',*/
        title: '',
        modal: true,
        width:'auto',
        close: function(event, ui) {
                $(this).dialog("destroy");
                $(this).remove();
        }
    }, options));

    /*if(typeof(options['help_text'])!="undefined")
    {
        $('a.ui-dialog-titlebar-close').clone(true)
                                       .appendTo($('a.ui-dialog-titlebar-close').parent())
                                       .children('span')
                                       .removeClass('ui-icon-closethick')
                                       .addClass('ui-icon-info')
                                       .css('margin-right','1em')
    }*/
}

creme.utils.bindShowHideTbody = function(root) {
    console.warn('this functions is deprecated. creme.blocks.bindEvents do the same work.');
    $('.table_detail_view', root).find('.collapser').each(function() {
        creme.blocks.bindTableToggle($(this));
    });
}

// TODO : only used by menu, so refactor it when horizontal menu will replace old one. 
creme.utils.confirmBeforeGo = function(url, ajax, ajax_options) { //TODO: factorise (see ajaxDelete()) ??
    creme.dialogs.confirm(gettext("Are you sure ?"))
                 .onOk(function() {
                     if (ajax) {
                         $.ajax(jQuery.extend({
                                   url: url,
                                   data: {},
                                   success: function(data, status, req) {
                                       creme.utils.reload(); //TODO: reload listview content instead (so rename the function)
                                   },
                                   error: function(req, status, error) {
                                       creme.dialogs.warning(req.responseText || gettext("Error")).open();
                                   },
                                   complete: function(request, textStatus) {},
                                   sync: false,
                                   //method: "GET",
                                   parameters : undefined
                               }, ajax_options)
                       );
                     } else {
                       creme.utils.goTo(url);
                     }
                  })
                 .open();
}

creme.utils.confirmSubmit = function(atag, msg) {
    creme.dialogs.confirm(msg || gettext('Are you sure ?'))
                 .onOk(function() {$('form', $(atag)).submit();})
                 .open();
}

if(typeof(creme.utils.stackedPopups)=="undefined") creme.utils.stackedPopups = [];//Avoid the re-declaration in case of reload of creme_utils.js

creme.utils.showInnerPopup = function(url, options, div_id, ajax_options, reload) {
    var reload_on_close = creme.object.isTrue(reload);
    var options = options || {};

    var $div = $('#' + div_id);
    if ($div.size() == 0) {
        var d = new Date();
        div_id = d.getTime().toString() + Math.ceil(Math.random() * 1000000);
        $div = $('<div id="' + div_id + '"  style="display:none;"></div>');
        $(document.body).append($div);
    }
    url += (url.indexOf('?') != -1) ? '&whoami=' + div_id: '?whoami=' + div_id; //TODO: use jquery method that builds URLs ?
    $.ajax(jQuery.extend({
        url: url,
        type: "GET",
        success: function(data) {
            creme.utils.stackedPopups.push('#' + div_id);
            creme.utils.showDialog(data,
                                   jQuery.extend({
                                       buttons: [{text: gettext("Cancel"),
                                                  click: function() { //$(this).dialog('close');
                                                             if (options !== undefined && $.isFunction(options.cancel)) {
                                                                 options.cancel($(this));
                                                             }

                                                             creme.utils.closeDialog($(this), reload_on_close);
                                                        }
                                                 }
                                                ],
                                       close: function(event, ui) {
                                           creme.utils.closeDialog($(this), false);
                                       },
                                       open: function(event, ui) {
                                            var $me = $(event.target);
                                            var $form = $('[name=inner_body]', $me).find('form');
                                            var send_button = options['send_button']; //function or boolean (if defined)

                                            // HACK : initialize widgets AFTER dialog opening.
                                            creme.widget.ready($me);

                                            if ($form.size() || send_button) {
                                                var submit_handler;

                                                if ($.isFunction(send_button)) {
                                                    submit_handler = function(e) {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        send_button($me);
                                                    };
                                                } else {
                                                    submit_handler = function(e) {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        creme.utils.handleDialogSubmit($me);
                                                    };
                                                }

                                                //$form.live('submit', function() {creme.utils.handleDialogSubmit($me);});

                                                var buttons = $me.dialog('option', 'buttons');
                                                //TODO: use the OS order for 'Cancel'/'OK' buttons
                                                buttons.unshift({text: options['send_button_label'] || gettext("Save"),
                                                                 click: submit_handler
                                                                }
                                                               );
                                                $me.dialog('option', 'buttons', buttons);
                                            }
                                       }
                                       //closeOnEscape: true
                                       //help_text : "Tape Escape to close."
                                   },options), div_id
           );
        },
        error: function(req, status, error) {
//             if (!req.responseText || req.responseText == "") {
//                 creme.utils.showDialog(gettext("Error during loading the page."));
//             } else {
//                 creme.utils.showDialog(req.responseText);
//             }
            creme.dialogs.warning(req.responseText || gettext("Error during loading the page.")).open();
        }
    }, ajax_options));

    return div_id;
}

creme.utils.handleDialogSubmit = function(dialog) {
    var div_id = dialog.attr('id');
    var $form = $('[name=inner_body]', dialog).find('form');
    var post_url = $('[name=inner_header_from_url]', dialog).val();

    var data = $form.serialize();
    if (data.length > 0) data += "&";
    data += "whoami=" + div_id;

    $.ajax({
          type: $form.attr('method'),
          url: post_url,
//          data : post_data,
          data: data,
          beforeSend: function(request) {
              creme.utils.loading('loading', false, {});
          },
          success: function(data, status) {
              is_closing = data.startsWith('<div class="in-popup" closing="true"')

              if (!is_closing) {
                  data += '<input type="hidden" name="whoami" value="' + div_id + '"/>';

                  creme.widget.shutdown(dialog);
                  $('[name=inner_body]', '#' + div_id).html(data);
                  creme.widget.ready(dialog);

                  creme.utils.scrollTo($('.errorlist:first', '.non_field_errors'));
              } else {
                  var content = $(data);
                  var redirect_url = content.attr('redirect');
                  var force_reload = content.is('[force-reload]');
                  var delegate_reload = content.is('[delegate-reload]');

                  if (redirect_url) {
                      creme.utils.closeDialog(dialog, force_reload, undefined, callback_url);
                  } else if (!delegate_reload) {
                      creme.utils.closeDialog(dialog, force_reload);
                  } else {
                      dialog.dialog('close');
                  }
              }
          },
          error: function(request, status, error) {
            creme.utils.showErrorNReload();
          },
          complete:function (XMLHttpRequest, textStatus) {
              creme.utils.loading('loading', true, {});
          }
    });

    return false;
}

creme.utils.scrollTo = function(element) {
    var position = $(element).position();

    if (Object.isNone(position) === false) {
        console.log(position);
        scrollTo(position.left, position.top);
    }
}

creme.utils.closeDialog = function(dial, reload, beforeReloadCb, callback_url) {
    $(dial).dialog("destroy");

    creme.widget.shutdown($(dial));
    $(dial).remove();

    creme.utils.stackedPopups.pop();//Remove dial from opened dialog array

//     if (beforeReloadCb != undefined && $.isFunction(beforeReloadCb)) {
    if ($.isFunction(beforeReloadCb))
        beforeReloadCb();

    // add by Jonathan 20/05/2010 in order to have a different callback url for inner popup if needs
    if (callback_url != undefined) {
        document.location = callback_url;
    } else if(reload) {
        creme.utils.reloadDialog(creme.utils.stackedPopups[creme.utils.stackedPopups.length-1] || window);//Get the dial's parent dialog or window
    }
}

creme.utils.reloadDialog = function(dial) {
    if (dial == window) {
        creme.utils.reload(window);
        return;
    }

    var reload_url = $(dial).find('[name=inner_header_from_url]').val();
    var div_id     = $(dial).find('[name=whoami]').val();

    reload_url += (reload_url.indexOf('?') != -1) ? '&whoami=' + div_id:
                                                    '?whoami=' + div_id;

    $.get(reload_url, function(data) { $(dial).html(data); });
}

creme.utils.appendInUrl = function(url, strToAppend) {
    var index_get = url.indexOf('?');
    var get = "", anchor = "";

    if (index_get > -1) {
        get = url.substring(index_get, url.length);
        url = url.substring(0, index_get);
    }
    var index_anchor = url.indexOf('#');
    if (index_anchor > -1) {
        anchor = url.substring(index_anchor, url.length);
        url = url.substring(0, index_anchor);
    }

    if (strToAppend.indexOf('?') > -1) {
        url += strToAppend+get.replace('?', '&');
    } else if (strToAppend.indexOf('&') > -1) {
        url += get + strToAppend;
    } else url += strToAppend + get;

    return url + anchor;
}

//TODO: move to a block.py ???
creme.utils.innerPopupNReload = function(url, reload_url) {
    creme.utils.showInnerPopup(url, {
        beforeClose: function(event, ui, dial) {
            creme.blocks.reload(reload_url);
        }
    });
}

creme.utils.handleResearch = function(target_node_id, from) {
    console.warn('creme.utils.handleResearch() functions is deprecated. Use creme.utils.decorateSearchResult() instead.');

    var research = $('[name=research]', from).val();

    $.ajax({
        url: '/creme_core/search',
        type: 'POST',
        data: {
                ct_id:    $('[name=ct_id]', from).val(),
                research: research
        },
        dataType: 'html',
        success: function(data, status, req) {
            var root = $('#' + target_node_id);
            root.html(data);
            creme.blocks.bindEvents(root); //initialize block (or pager and co do not work)

            //highlight the word that we are searching
            research = research.toLowerCase();
//             $('div.result').find("td, td *")
            root.find('.search_result')
                .contents()
                .filter(function() {
                        if (this.nodeType != Node.TEXT_NODE) return false;
                        return this.textContent.toLowerCase().indexOf(research) >= 0;
                    })
                .wrap($('<mark/>'));

            // we update the title ; this is done on client side because pagination is done in the template rendering
            // and we want to avoid making the count() queries twice.
            var total = 0;
            root.find('[search-count]').each(function() {
                total += parseInt(this.getAttribute('search-count'));
            });
            root.find('#search_results_title')
                .text(ngettext('Search results: %d entity', 'Search results: %d entities', total).format(total));
        },
        error: function(req, status, errorThrown) {
        },
        complete: function() {
            document.title = gettext("Search results…");
        }
    });
}

creme.utils.decorateSearchResult = function(research) {
    $('.search_results').each(function() {
        var root = $(this);

        //highlight the word that we are searching
        research = research.toLowerCase();
        root.find('.search_result')
            .contents()
            .filter(function() { return $(this).text().toLowerCase().indexOf(research) >= 0; })
            .wrap($('<mark/>'));

        // we update the title ; this is done on client side because pagination is done in the template rendering
        // and we want to avoid making the count() queries twice.
        var total = 0;
        root.find('[search-count]').each(function() {
            total += parseInt(this.getAttribute('search-count'));
        });
        root.find('#search_results_title')
            .text(ngettext('Search results: %d entity', 'Search results: %d entities', total).format(total));
    });
}

creme.utils.openQuickForms = function(element) {
    var uri = '/creme_core/quickforms/%s/%s';
    var type = $('[name="ct_id"]', element).val();
    var count = $('[name="entity_count"]', element).val();

    creme.dialogs.form(uri.format(type, count), {reloadOnSuccess: true}).open();
}

creme.utils.autoCheckallState = function(from, select_all_selector, checkboxes_selector) {
    var $select_all = $(select_all_selector);

    if (!$(from).is(':checked')) {
        $select_all.uncheck();
        return;
    }

    var all_checked = true;
    $(checkboxes_selector).each(function() {
        all_checked = all_checked & $(this).is(':checked');
    });

    if (all_checked) {
        $select_all.check();
    } else {
        $select_all.uncheck();
    }
};

creme.utils.toggleCheckallState = function(select_all, checkboxes_selector) {
    if ($(select_all).is(':checked')) {
        $(checkboxes_selector).check();
    } else {
        $(checkboxes_selector).uncheck();
    }
};

creme.utils.showErrorNReload = function() {
    creme.dialogs.warning('<p><b>' + gettext("Error !") + '</b></p><p>' + gettext("The page will be reload !") + '</p>')
                 .open();

    setTimeout(creme.utils.reload, 3000);
};

creme.utils.confirmPOSTQuery = function(url, options, data) {
    return creme.utils.confirmAjaxQuery(url, $.extend({action:'post'}, options), data);
}

creme.utils.confirmAjaxQuery = function(url, options, data) {
    var options = $.extend({action: 'get', warnOnFail: true}, options || {});
    var message = options.confirm || gettext("Are you sure ?");

    var action = new creme.component.Action(function() {
        var self = this;
        var query = creme.ajax.query(url, options, data);

        query.onFail(function(event, error, status) {
                  if (options.warnOnFail) {
                      var message = Object.isType(error, 'string') ? error : (error.message || gettext("Error"));
                      creme.dialogs.error(message, {title: options.warnOnFailTitle}, status)
                                   .onClose(function() {self.fail(error, status);})
                                   .open();
                  } else {
                      self.fail(error, status)
                  }
              })
             .onDone(function(event, result) {
                  if (options.messageOnSuccess) {
                      creme.dialogs.html('<p>%s</p>'.format(options.messageOnSuccess))
                                   .onClose(function() {self.done(result)})
                                   .open()
                  } else {
                      self.done(result);
                  }
              });

        if (options.waitingOverlay) {
            query.onStart(function() {creme.utils.showPageLoadOverlay();});
            query.onComplete(function() {creme.utils.hidePageLoadOverlay();});
        }

        creme.dialogs.confirm('<h4>%s</h4>'.format(message))
                     .onOk(function() {query.start();})
                     .onClose(function() {self.cancel();})
                     .open({width:250, height:150});
    }, options);

    if (options.reloadOnSuccess) {
        action.onDone(function(event, data) {creme.utils.reload();});
    }

    return action;
}

creme.utils.ajaxQuery = function(url, options, data) {
    var options = $.extend({action: 'get', warnOnFail:true}, options || {});
    var query = creme.ajax.query(url, options, data);

    if (options.warnOnFail) {
        query.onFail(function(event, error, status) {
                  var message = Object.isType(error, 'string') ? error : (error.message || gettext("Error"));
                  creme.dialogs.error(message, {title: options.warnOnFailTitle}, status)
                               .onClose(function() {
                                   if (options.reloadOnFail) {
                                       creme.utils.reload();
                                   }
                                })
                               .open();
              });
    } else if (options.reloadOnFail) {
        query.onFail(function(event, data) {creme.utils.reload();});
    }

    if (options.messageOnSuccess)
    {
        query.onDone(function(event, data) {
                  creme.dialogs.html('<p>%s</p>'.format(options.messageOnSuccess))
                               .onClose(function() {
                                    if (options.reloadOnSuccess) {
                                        creme.utils.reload();
                                    }
                                })
                               .open();
              });
    } else if (options.reloadOnSuccess) {
        query.onDone(function(event, data) {creme.utils.reload();});
    }

    if (options.waitingOverlay) {
        query.onStart(function() {creme.utils.showPageLoadOverlay();});
        query.onComplete(function() {creme.utils.hidePageLoadOverlay();});
    }

    return query;
};

creme.utils.innerPopupFormAction = function(url, options, data) {
    var options = $.extend({
                      submit_label: gettext("Save"),
                      submit: function(dialog) {
                          creme.utils.handleDialogSubmit(dialog);
                      },
                      reloadOnSuccess: false
                  }, options || {});

    return new creme.component.Action(function() {
        var self = this;

        creme.utils.showInnerPopup(url,
                                   {
                                       send_button_label: options.submit_label,
                                       send_button: function(dialog) {
                                           try {
                                               var submitdata = options.submit.apply(this, arguments);

                                               if (submitdata && Object.isFunc(options.validator) && options.validator(submitdata))
                                               {
                                                   self.done(submitdata);
                                                   creme.utils.closeDialog(dialog, options.reloadOnSuccess);
                                               }
                                           } catch(e) {
                                               self.fail(e);
                                           }
                                       },
                                       cancel: function(event, ui) {
                                           self.cancel();
                                       },
                                       close: function(event, ui) {
                                           creme.utils.closeDialog($(this), false);
                                           self.done();
                                       }
                                   },
                                   null,
                                   {
                                       error: function(req, status, error) {
                                           try {
                                               creme.dialogs.warning(gettext("Error during loading the page.")).open();
                                               self.fail(req, status, error);
                                           } catch(e) {
                                               self.fail(req, status, error);
                                           }
                                       },
                                       data: data
                                   });
    });
}
