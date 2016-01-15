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

creme.blocks = {
    collapsed_class:    'collapsed',
    hide_fields_class:  'hide_empty_fields',
    status_stave_delay: 500
};

creme.blocks.reload = function(url) {
    creme.ajax.query(url, {backend: {sync: false, dataType: 'json'}})
              .onDone(function(event, data) {
                  data.forEach(function(entry) {
                      // upgrade to Jquery 1.9x : html content without starting '<' is no longer supported.
                      //                          use $.trim() for trailing space or returns.
                      creme.blocks.fill($('[id="' + entry[0] + '"]'), $($.trim(entry[1]))); 
                  });
               })
              .start();
};

creme.blocks.fill = function(block, content) {
    block.replaceWith(content);
    creme.blocks.initialize(content);
};

// TODO : make a generic method for deferred save. something like:
//        deferredAction(element, action_name, action_func, action_delay)
creme.blocks.saveState = function(block) {
    var state = {
            is_open:           $(block).hasClass('collapsed') ? 0 : 1,
            show_empty_fields: $(block).hasClass(this.hide_fields_class) ? 0 : 1
    };

    var previous = block.data('block-deferred-save');

    if (previous !== undefined)
        previous.reject();

    var deferred = $.Deferred();

    $.when(deferred.promise()).then(function(status) {
        block.removeData('block-deferred-save');
        creme.ajax.json.post('/creme_core/blocks/reload/set_state/' + block.attr('id') + '/',
                             state, null, null, true);
    }, null, null);

    block.data('block-deferred-save', deferred);

    window.setTimeout(function() {
        deferred.resolve();
    }, this.status_stave_delay);
};

creme.blocks.initEmptyFields = function(block) {
    // if there are no buttons toggling the 'empty field hiding', we should do nothing with the block lines
    if (block.find ('.block_header .buttons').find ('a.view_less, a.view_more').length == 0)
        return;

    $('tbody > tr.content', block).not(':has(> td:not(.edit_inner):not(:empty))').addClass('collapsable-field');
    creme.blocks.updateFieldsColors(block);
    creme.blocks.updateToggleButton(block);
};

creme.blocks.updateFieldsColors = function(block) {
    var line_collapsed = block.hasClass(this.hide_fields_class);

    if (!line_collapsed) {
        $('tbody > tr.content:even td', block).toggleClass('block_line_light', true).toggleClass('block_line_dark', false);
        $('tbody > tr.content:odd td', block).toggleClass('block_line_light', false).toggleClass('block_line_dark', true);

        $('tbody > tr.content:even th', block).toggleClass('block_header_line_light', true).toggleClass('block_header_line_dark', false);
        $('tbody > tr.content:odd th', block).toggleClass('block_header_line_light', false).toggleClass('block_header_line_dark', true);
    } else {
        $('tbody > tr.content:not(.collapsable-field):even td', block).toggleClass('block_line_light', true).toggleClass('block_line_dark', false);
        $('tbody > tr.content:not(.collapsable-field):odd td', block).toggleClass('block_line_light', false).toggleClass('block_line_dark', true);

        $('tbody > tr.content:not(.collapsable-field):even th', block).toggleClass('block_header_line_light', true).toggleClass('block_header_line_dark', false);
        $('tbody > tr.content:not(.collapsable-field):odd th', block).toggleClass('block_header_line_light', false).toggleClass('block_header_line_dark', true);
    }
}

creme.blocks.updateToggleButton = function(block, collapsed) {
    var button = $('table.block_header th.actions a.view_more, table.block_header th.actions a.view_less', block);
    var collapsed = block.hasClass(this.hide_fields_class);
    var button_title = collapsed ? gettext('Show empty fields') : gettext('Hide empty fields');

    button.toggleClass('view_less', !collapsed).toggleClass('view_more', collapsed);
    button.attr('title', button_title)
          .attr('alt', button_title);
}

creme.blocks.toggleEmptyFields = function(button) {
    var $block = $(button).parents('table[id].table_detail_view:not(.collapsed)');

    if ($block.size() == 0)
        return;

    var previous_state = $block.hasClass(this.hide_fields_class);

    $block.toggleClass(this.hide_fields_class);

    creme.blocks.updateFieldsColors($block);
    creme.blocks.updateToggleButton($block);

    $block.trigger('creme-blocks-field-display-changed', {action : previous_state ? 'show' : 'hide'});
};

creme.blocks.initPager = function(pager) {
    // TODO : remove this hack when smartlinks will be available.
    $('.pager-link a', pager).bind('click', function(e) {
        e.preventDefault();

        if ($(this).is('[disabled]'))
            return;

        var url = creme.utils.lambda($(this).attr('data-page-uri'))();
        creme.blocks.reload(url);
    });

    var cleanPage = function(input) {
        var page = parseInt(input.val());
        var max = parseInt(input.attr('max'))

        if (isNaN(page) || page < 1 || (!isNaN(max) && page > max))
            return false;

        return page;
    }

    var gotoPage = function(input) {
        var page = cleanPage(input);

        if (page !== false) {
            creme.blocks.reload(creme.utils.lambda(input.attr('data-page-uri'), 'page')(page));
        }
    }

    var resizeInput = function(element) {
        var canvas2d = element.data('creme-block-pager-canvas');

        if (canvas2d === undefined) {
            canvas2d = document.createElement('canvas').getContext("2d");
            element.data('creme-block-pager-canvas', canvas2d);
        }

        var value = element.val() !== null ? element.val() : '';
        canvas2d.font = element.css('font-size') + ' ' + element.css('font-family');
        var width = canvas2d.measureText(value).width;

        element.css('width', width + 20);
    }

    $('.pager-input', pager).each(function() {
        var input = $(this);
        var selector = $('input', input);

        input.click(function(e) {
            e.stopPropagation();
            $(this).addClass('active')

            resizeInput(selector);

            selector.toggleClass('invalid-page', cleanPage(selector) === false)
                    .select().focus();
        });

        selector.bind('propertychange input change paste', function(e) {
            creme.object.deferred_start(pager, 'creme-block-pager-change', function() {
                //gotoPage(selector);
                selector.toggleClass('invalid-page', cleanPage(selector) === false);
            }, 300);
        }).bind('propertychange input change paste keydown', function() {
            resizeInput(selector);
        }).bind('keyup', function(e) {
            if (e.keyCode === 13) {
                e.preventDefault();
                creme.object.deferred_cancel(pager, 'creme-block-pager-change');
                gotoPage($(this));
            } else if (e.keyCode === 27) {
                e.preventDefault();
                creme.object.deferred_cancel(pager, 'creme-block-pager-change');
                selector.focusout();
            }
        }).bind('focusout', function() {
            creme.object.deferred_cancel(pager, 'creme-block-pager-change');
            input.removeClass('active');
        });
    });
}

creme.blocks.initialize = function(block) {
    block.bind('creme-table-collapse', function(e, params) {
        creme.blocks.saveState($(this));
    });

    block.bind('creme-blocks-field-display-changed', function(e, params) {
        creme.blocks.saveState($(this));
    });

    block.find('.collapser').each(function() {
        creme.blocks.bindTableToggle($(this));
    });

    $('.creme-block-pager', block).each(function() {
        creme.blocks.initPager($(this));
    });

    creme.blocks.initEmptyFields(block);
    creme.widget.ready(block);
    block.trigger('block-ready', [block]);
};

creme.blocks.bindEvents = function(root) {
    $('.table_detail_view[id]:not(.block-ready)', root).each(function() {
        var block = $(this);

        try {
            creme.blocks.initialize(block);
            block.addClass('block-ready');
        } catch(e) {
            console.warn('unable to initialize block', block.attr('id'), ':', e);
        }
    });
};

creme.blocks.scrollToError = function(block) {
    creme.utils.scrollTo($('.errorlist:first'));
}

creme.blocks.form = function(url, options, data) {
    var options = options || {};
    var dialog = creme.dialogs.form(url, options, data);

    if (options.blockReloadUrl) {
        dialog.onFormSuccess(function() {
                  creme.blocks.reload(options.blockReloadUrl);
               });
    }

    return dialog;
};

creme.blocks.confirmPOSTQuery = function(url, options, data) {
    return creme.blocks.confirmAjaxQuery(url, $.extend({action: 'post'}, options), data);
}

creme.blocks.confirmAjaxQuery = function(url, options, data) {
    var action = creme.utils.confirmAjaxQuery(url, options, data);

    if (options.blockReloadUrl) {
        action.onComplete(function(event, data) {
                  creme.blocks.reload(options.blockReloadUrl);
               });
    }

    return action;
};

creme.blocks.ajaxPOSTQuery = function(url, options, data) {
    return creme.blocks.ajaxQuery(url, $.extend({action: 'post'}, options), data);
}

creme.blocks.ajaxQuery = function(url, options, data) {
    var query = creme.utils.ajaxQuery(url, options, data);

    if (options.blockReloadUrl) {
        query.onComplete(function(event, data) {
                 creme.blocks.reload(options.blockReloadUrl);
              });
    }

    return query;
};

creme.blocks.massAction = function(url, selector, block_url, values_post_process_cb) {
    var values = $(selector).getValues();

    if ($.isFunction(values_post_process_cb)) {
        values = values_post_process_cb(values);
    }

    if (values.length == 0) {
        creme.dialogs.warning(gettext("Nothing is selected.")).open();
        return;
    }

    creme.blocks.confirmPOSTQuery(url,
                                  {blockReloadUrl: block_url,
                                   messageOnSuccess: gettext('Process done')
                                  },
                                  {ids: values})
                .start();
};

creme.blocks.massRelation = function(subject_ct_id, rtype_ids, selector, block_url) {
    var values = $(selector).getValues();
    if (values.length == 0) {
        creme.dialogs.warning(gettext("Please select at least one entity.")).open();
        return false;
    }

    url = '/creme_core/relation/add_to_entities/%s/%s/'.format(subject_ct_id, rtype_ids.join(','));
    url += '?' + $.param({persist: 'id', ids: values})

    creme.blocks.form(url, {blockReloadUrl: block_url}).open();
};

creme.blocks.tableExpandState = function($self, state, trigger) {
    var $table = $self.parents('table[id]');
    var $collapsable = $table.find('.collapsable');

    var old_state = !$table.hasClass('collapsed');

    if (state === old_state)
        return;

    $table.toggleClass('collapsed faded', !state);

    if (trigger === undefined || trigger) {
        $table.trigger('creme-table-collapse', {action: state ? 'show' : 'hide'});

        if (state === true) {
            $('.ui-creme-resizable', $table).trigger('resize')
                                            .trigger('resizestop');
        }
    }
}

creme.blocks.tableIsCollapsed = function($self) {
    return $self.parents('table[id]').hasClass('collapsed');
}

creme.blocks.tableExpand = function($self, trigger) {
    creme.blocks.tableExpandState($self, true, trigger);
}

creme.blocks.bindTableToggle = function($self) {
    $self.click(function(e) {
        // HACK: we avoid that clicking on a button in the header collapses the block;
        //       we should stop the propagation of the event in the buttons => we _really_ need to refactor the button system.
        if ($(e.target).parent('.buttons').length > 0)
            return;

        creme.blocks.tableExpandState($self, creme.blocks.tableIsCollapsed($self));
    });
}
