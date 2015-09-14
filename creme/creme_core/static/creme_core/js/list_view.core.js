/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2010  Hybird

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
/*
 * Dependencies : jQuery / jquery.utils.js
 */

//TODO : To be deleted and all console.log in code also

(function($) {
    $.fn.list_view = function(options) {

        var isMethodCall = (typeof options == 'string'),
            args = Array.prototype.slice.call(arguments, 1);

        $.fn.list_view.defaults = {
            user_page         : '#user_page',
            selected_rows     : '#selected_rows',
            selectable_class  : 'selectable',
            selected_class    : 'selected',
            id_container      : '[name="entity_id"]',
            checkbox_selector : '[name="select_one"]',
            all_boxes_selector: '[name="select_all"]',
            beforeSubmit      : null,
            afterSubmit       : null,
            o2m               : false,
            entity_separator  : ',',
            serializer        : 'input[name][type!="submit"], select[name]',
            submitHandler     : null,//Use handleSubmit in it to easy list view's management
            kd_submitHandler  : null,//Same as submitHandler but for key down events,
            reload_url        : null
        };

        var publicMethods = ["countEntities", "getSelectedEntities",
                             "getSelectedEntitiesAsArray",
                             "option", "serializeMe", "ensureSelection",
                             "getSubmit", "getKdSubmit",
                             "setSubmit", "setKdSubmit",
                             "setReloadUrl", "getReloadUrl", "isLoading"];

        if (isMethodCall && $.inArray(options, publicMethods) > -1) {
                var instance = $.data(this[0], 'list_view');
                return (instance ? instance[options].apply(instance, args)
                        : undefined);
        }

        return this.each(function() {

            // constructor
            if(!isMethodCall) {
                var opts = $.extend($.fn.list_view.defaults, options);
                var selected_ids = [];
                var self = $(this);
                var me = this;

                $.data(this, 'list_view', this);

                me.beforeSubmit     = ($.isFunction(opts.beforeSubmit))     ? opts.beforeSubmit     : false;
                me.afterSubmit      = ($.isFunction(opts.afterSubmit))      ? opts.afterSubmit      : false;
                me.submitHandler    = ($.isFunction(opts.submitHandler))    ? opts.submitHandler    : false;
                me.kd_submitHandler = ($.isFunction(opts.kd_submitHandler)) ? opts.kd_submitHandler : false;
                me.is_loading = false;

                /*me.user_page          = opts.user_page;
                me.selected_rows      = opts.selected_rows;
                me.selectable_class   = opts.selectable_class;
                me.selected_class     = opts.selected_class;
                me.id_container       = opts.id_container;
                me.checkbox_selector  = opts.checkbox_selector;
                me.all_boxes_selector = opts.all_boxes_selector;
                me.o2m                = opts.o2m;
                me.entity_separator   = opts.entity_separator;
                me.serializer         = opts.serializer;*/


                /***************** Getters & Setters *****************/
                this.getSelectedEntities = function() {
                    return $(opts.selected_rows, self).val();
                }

                this.getSelectedEntitiesAsArray = function() {
                    return ($(opts.selected_rows, self).val()!=="") ? $(opts.selected_rows, self).val().split(opts.entity_separator) : [];
                }

                this.countEntities = function() {
                    return ($(opts.selected_rows, self).val()!=="") ? $(opts.selected_rows, self).val().split(opts.entity_separator).length : 0;
                }

                this.option = function(key, value){
                    if (typeof key == "string") {
                        if (value === undefined) {
                            return opts[key];
                        }
                        opts[key] = value;
                    }
                }

                this.setSubmit = function(fn) {
                    if($.isFunction(fn)) me.submitHandler = fn;
                }

                this.setKdSubmit = function(fn) {
                    if($.isFunction(fn)) me.kd_submitHandler = fn;
                }

                this.getSubmit = function() {
                    if(me.submitHandler) return me.submitHandler;
                    return function(){};//Null handler
                }

                this.getKdSubmit = function() {
                    if(me.kd_submitHandler) return me.kd_submitHandler;
                    return function(){};//Null handler
                }

                this.setReloadUrl = function(url) {
                    me.reload_url = url;
                }

                this.getReloadUrl = function() {
                    return me.reload_url;
                }

                this.isLoading = function() {
                    return me.is_loading;
                }

                /***************** Helpers ****************************/
                this.reload = function(is_ajax) {

                    var url = this.reload_url || creme.utils.appendInUrl(window.location.href,'?ajax='+(is_ajax || true));

                    var submit_opts = {
                        'action': url,
                        'success':function(data, status){
                            self.empty().html(data);
                        }
                    };

//                    self.list_view('handleSubmit', null, submit_opts, null);
                    this.handleSubmit(null, submit_opts, null);
                }

                this.hasSelection = function() {
                    return (this.countEntities() != 0);
                }

                this.ensureSelection = function() {
                    if(!this.hasSelection()) {
                        creme.dialogs.warning(gettext("Please select at least one entity."));
                        return false;
                    }
                    return true;
                }

                this.enableFilters = function() {
                    self.find('.columns_bottom .column input[type="text"]')
                        .bind('keydown', function(event) {
                             event.stopPropagation();
                             me.getKdSubmit()(event, this, {'_search': 1});
                         });

                    self.find('.columns_bottom .column select')
                        .bind('change', function(event) {
                             event.stopPropagation();
                             me.getSubmit()(this, {'_search': 1});
                         });

                    self.find('.columns_bottom .column.datefield input')
                        .bind('keydown', function(event) {
                             event.stopPropagation();
                             me.getKdSubmit()(event, this, {'_search': 1});
                         })
                        .datepicker({dateFormat: "yy-mm-dd",
                                     showOn:     "both",
                                     buttonImage: creme_media_url('images/icon_calendar.gif'),
                                     buttonImageOnly: true});
                }

                this.enableActions = function() {
                    self.find('.lv-header-action-list').NavIt({ArrowSideOnRight: false});
                    self.find('.lv-action-toggle')
                        .click(function() {
                            $(this).parents('ul').find('ul').slideToggle('slide');
                         });

                    creme.menu.HNavIt(self.find('.lv-row-action-list'), {}, {
                        done: function() {
                            if (this.options().link.is('.lv_reload')) {
                                me.reload();
                            }
                        }
                    });
                }

                /***************** Row selection part *****************/
                this.enableRowSelection = function() {
                    self.find('.'+opts.selectable_class)
                    //.live('click',
                    .bind('click',
                        function(e) {
                            var entity_id = $(this).find(opts.id_container).val();
                            var entity_id_index = $.inArray(entity_id, selected_ids);//selected_ids.indexOf(entity_id);

                            if(!$(this).hasClass(opts.selected_class)) {
                                if(entity_id_index === -1) {
                                    if(opts.o2m){
                                        selected_ids = [];
                                        self.find('.'+opts.selected_class).removeClass(opts.selected_class);
                                    }
                                    selected_ids.push(entity_id);
                                    $(opts.selected_rows).val(selected_ids.join(opts.entity_separator));
                                }
                                if(!$(this).hasClass(opts.selected_class))$(this).addClass(opts.selected_class);
                                if(!opts.o2m) {
                                    $(this).find(opts.checkbox_selector).check();
                                }
                            } else {
                                self.find(opts.all_boxes_selector).uncheck();
                                if(entity_id_index !== -1) selected_ids.splice(entity_id_index, 1);
                                $(opts.selected_rows).val(selected_ids.join(opts.entity_separator));
                                if($(this).hasClass(opts.selected_class))$(this).removeClass(opts.selected_class);
                                if(!opts.o2m) {
                                    $(this).find(opts.checkbox_selector).uncheck();
                                }
                            }
                        }
                    );
                }

                // Firefox keeps the checked state of inputs on simple page reloads
                // we could 1) incorporate those pre-selected rows into our initial selected_ids set
                //          2) force all checkboxes to be unchecked by default. Either in js here, or
                //             possibly in HTML (maybe by using lone inputs instead of having them in a <form>)
                this.clearRowSelection = function() {
                    $(opts.selected_rows).val('');

                    // upgrade to Jquery 1.9x : "checked" is a property and attr() method should not be used.
                    self.find('.' + opts.selectable_class + ' .choices input[type="checkbox"],' +
                              opts.all_boxes_selector)
                        .prop('checked', false);
                }
                /******************************************************/

                /***************** Check all boxes part *****************/
                this.enableCheckAllBoxes = function() {
//                    self.find(opts.all_boxes_selector).live('click',
                    self.find(opts.all_boxes_selector)
                    .bind('click',
                        function(e) {
                            var entities = self.find('.'+opts.selectable_class);
                            if($(this).is(':checked')) {
                                entities.each(function() {
                                    var entity_id = $(this).find(opts.id_container).val();
                                    var entity_id_index = $.inArray(entity_id, selected_ids);//selected_ids.indexOf(entity_id);
                                    if(entity_id_index === -1) {
                                        selected_ids.push(entity_id);
                                    }
                                    if(!$(this).hasClass(opts.selected_class))$(this).addClass(opts.selected_class);
                                    if(!opts.o2m) {
                                        $(this).find(opts.checkbox_selector).check();
                                    }
                                });
                                $(opts.selected_rows).val(selected_ids.join(opts.entity_separator));
                            } else {
                                entities.each(function() {
                                    if($(this).hasClass(opts.selected_class))$(this).removeClass(opts.selected_class);
                                    if(!opts.o2m){
                                        $(this).find(opts.checkbox_selector).uncheck();
                                    }
                                });
                                selected_ids = [];
                                $(opts.selected_rows).val('');
                            }
                        }
                    );
                }

                /******************************************************/

                /***************** Submit part *****************/

                //Remove this part in ajax lv for handling multi-page selection,
                //if that you want implement the "coloration" selection on submit
                this.flushSelected = function() {
                    $(opts.selected_rows, self).val('');
                    selected_ids = [];
                }

                this.disableEvents = function() {
//                    self.find('.'+opts.selectable_class).die('click');
//                    if(!opts.o2m) self.find(opts.all_boxes_selector).die('click');
                    self.find('.'+opts.selectable_class).unbind('click');
                    if(!opts.o2m) self.find(opts.all_boxes_selector).unbind('click');
                }

                this.enableEvents = function() {
                    this.enableRowSelection();
                    this.enableFilters();
                    this.enableActions();
                    if(!opts.o2m) this.enableCheckAllBoxes();
                }

//                this.serializeMe = function (){
//                    var data = {};
//                    self.find(opts.serializer).each(function(){
//                       var $node = $(this);
//                       data[$node.attr('name')] = $node.val();
//                    });
//                    return data;
//                }

                this.serializeMe = function () {
                    var data = {};
                    self.find(opts.serializer).each(function() {
                       var $node = $(this);
                       if(typeof(data[$node.attr('name')]) == "undefined") {
                           data[$node.attr('name')] = [$node.val()];
                       } else if(data[$node.attr('name')].length > 0) {
                           data[$node.attr('name')].push($node.val());
                       }
                    });
                    return data;
                }

                this.handleSubmit = function(form, options, target, extra_data) {
                    if (me.is_loading) {
                        return;
                    } 

                    var data = this.serializeMe();
                    if(typeof(extra_data)!="undefined") {
                        data = $.extend(data, extra_data);
                    }

                    var $target = $(target);
//                    data[$target.attr('name')] = $target.val();

                    if(typeof(data[$target.attr('name')]) == "undefined"){
                        data[$target.attr('name')] = [$target.val()];
                    }
                    else if(data[$target.attr('name')].length > 0){
                        var target_value = $target.val();
                        if($.inArray(target_value, data[$target.attr('name')]) == -1)
                            data[$target.attr('name')].push(target_value);
                    }

                    if(typeof(data['page']) == "undefined") {
                        data['page'] = $(opts.user_page, self);
                    }

                    this.disableEvents();
                    me.is_loading = true;

                    //We get a previous beforeComplete user callback if exists
                    var previousCallback = null;
                    if(typeof(options) !== "undefined" && typeof(options['beforeComplete']) == "function") {
                        previousCallback = options['beforeComplete'];
                    }

                    options['beforeComplete'] = function(request, status) {
                        //Calling our beforeComplete callback
                        me.is_loading = false;
                        self.list_view('enableEvents');
                        //Then user callback
                        if(previousCallback) previousCallback(request, status);
                    }

                    creme.ajax.submit(form, data, options);
                    this.flushSelected();
                }

                this.init = function() {
                    this.clearRowSelection();
                    this.enableEvents();
                }

                this.init();
            } else {
                if($.isFunction(this[options])) this[options].apply(this, args);
            }
        });
    };//$.fn.list_view
})(jQuery);
