/*******************************************************************************
    Creme is a free/open-source Customer Relationship Management software
    Copyright (C) 2009-2013  Hybird

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

(function($) {"use strict";

creme.model = creme.model || {};

creme.model.ChoiceRenderer = creme.model.ListRenderer.sub({
    createItem: function(target, before, data, index)
    {
        var item = $('<option>');
        this.updateItem(target, item, data, undefined, index);
        return item;
    },

    updateItem: function(target, item, data, previous, index, action)
    {
        if (action === 'select')
            return this.selectItem(target, item, data, previous, index);

        var value = Object.isNone(data.value) ? '' : data.value;

        if (typeof data.value === 'object')
            value = new creme.utils.JSON().encode(data.value)

        // upgrade to Jquery 1.9x : selected is a property and attr() method should not be used.
        item.attr('value', value)
            .toggleAttr('disabled', data.disabled === true)
            .prop('selected', data.selected === true)
            .toggleAttr('tags', data.tags, (data.tags || []).join(' '))
            .html(data.label);
    },

    selectItem: function(target, item, data, previous, index) {
        // upgrade to Jquery 1.9x : selected is a property and attr() method should not be used.
        item.prop('selected', data.selected === true);
    },

    items: function(target) {
        return $('option', target);
    }
});

creme.model.ChoiceRenderer.parse = function(element, converter) { 
    var values = element.val();
    values = element.is('[multiple]') ? (values || []) : [values];

    return $('option', element).map(function() {
        var option = $(this);
        var option_value = option.attr('value');

        return {
            label:    option.html(),
            value:    Object.isFunc(converter) ? converter(option_value) : option_value,
            disabled: option.is('[disabled]'),
            selected: values.indexOf(option_value) !== -1,
            visible:  true,
            help:     option.attr('help'),
            tags:     option.is('[tags]') && option.attr('tags') ? option.attr('tags').split(' ') : []
        };
    }).get();
};

creme.model.ChoiceRenderer.choicesFromTuples = function(data) {
    var data = data || [];
    var istuple = data ? Array.isArray(data[0]) : false;

    if (istuple) {
        return data.map(function(entry) {
            return {value: entry[0], label: entry[1], visible: true, disabled: false, selected: false};
        });
    } else {
        return data.map(function(entry) {
            return {value: entry, label: '' + entry, visible: true, disabled: false, selected: false};
        });
    }
};

creme.model.ChoiceGroupRenderer = creme.model.ChoiceRenderer.sub({
    insertGroup: function(target, before, groupname)
    {
        var group = $('optgroup[label="' + groupname + '"]', target);

        if (group && group.length) {
            return group;
        }

        group = $('<optgroup label="' + groupname + '">');

        if (before && before.length) {
            before.parent().before(group);
        } else {
            target.append(group);
        }

        return group;
    },

    insertItem: function(target, before, data, index)
    {
        var group = target;
        var previous_groupname = before && before.length ? before.parent().attr('label') : undefined;
        var next_groupname = data.group;

        if (next_groupname) {
            group = this.insertGroup(target, before, next_groupname);
        }

        if (before && before.length)
        {
            if (next_groupname && previous_groupname !== next_groupname) {
                before = $('option:first', group);
            }

            before.before(this.createItem(target, before, data, index));
        } else {
            group.append(this.createItem(target, before, data, index));
        }
    },

    removeItem: function(target, item, data, index)
    {
        var group = data.group ? item.parent() : undefined;

        item.remove();

        if (group && $('option', group).length < 1)
            group.remove();
    },

    updateItem: function(target, item, data, previous, index, action)
    {
        if (action === 'select')
            return this.selectItem(target, item, data, previous, index);

        var group = target;
        var prev_group = item.parent();

        var previous_groupname = previous ? previous.group : undefined;
        var next_groupname = data.group;

        if (next_groupname) {
            group = this.insertGroup(target, item.next(), next_groupname);
        }

        if (previous_groupname !== next_groupname)
        {
            item.remove();
            group.append(item);

            if (prev_group && ($('option', prev_group).length) < 1)
                prev_group.remove();
        }

        var value = Object.isNone(data.value) ? '' : data.value;

        if (typeof data.value === 'object')
            value = new creme.utils.JSON().encode(data.value)

        // upgrade to Jquery 1.9x : selected is a property and attr() method should not be used.
        item.attr('value', value)
            .toggleAttr('disabled', data.disabled === true)
            .prop('selected', data.selected === true)
            .toggleAttr('tags', data.tags, (data.tags || []).join(' '))
            .html(data.label);
    }
});

creme.model.ChoiceGroupRenderer.parse = function(element, converter) {
    var values = element.val();
    values = element.is('[multiple]') ? (values || []) : [values]; 

    return $('option', element).map(function() {
        var option = $(this);
        var option_value = option.attr('value');
        var option_group = option.parent();

        return {
            group:    (option_group && option_group.is('optgroup')) ? option_group.attr('label') : undefined,
            label:    option.html(),
            value:    Object.isFunc(converter) ? converter(option_value) : option_value,
            disabled: option.is('[disabled]'),
            selected: values.indexOf(option_value) !== -1,
            visible:  true,
            help:     option.attr('help'),
            tags:     option.is('[tags]') && option.attr('tags') ? option.attr('tags').split(' ') : []
        };
    }).get();
};

creme.model.ChoiceGroupRenderer.choicesFromTuples = function(data) {
    var data = data || [];
    var istuple = data ? Array.isArray(data[0]) : false;

    if (istuple) {
        return data.map(function(entry) {
            if (entry.length > 2) {
                return {value: entry[0], label: entry[1], group: entry[2], visible: true, disabled: false, selected: false};
            } else {
                return {value: entry[0], label: entry[1], group: undefined, visible: true, disabled: false, selected: false};
            }
        });
    } else {
        return data.map(function(entry) {
            return {value: entry, label: '' + entry, group: undefined, visible: true, disabled: false, selected: false};
        });
    }
};

creme.model.CheckListRenderer = creme.model.ListRenderer.sub({
    _init_: function(options)
    {
        var options = $.extend({itemtag: 'li', disabled: false}, options || {});

        this._super_(creme.model.ListRenderer, '_init_');
        this._itemtag = options.itemtag;
        this._disabled = options.disabled;
    },

    disabled: function(disabled) {
        return Object.property(this, '_disabled', disabled);
    },

    _getItemValue: function(data) {
        var value = Object.isNone(data.value) ? '' : data.value;

        if (typeof data.value === 'object') {
            value = new creme.utils.JSON().encode(data.value);
        }

        return value;
    },

    createItem: function(target, before, data, index)
    {
        var disabled = data.disabled || this._disabled;
        var value = this._getItemValue(data);

        var context = {
            tag: this._itemtag,
            disabled: disabled ? 'disabled' : '',
            value: value,
            index: index,
            checked: data.selected ? 'checked': '',
            label: data.label || '',
            help: data.help || '',
            hidden: !data.visible ? 'hidden' : '',
            tags: (data.tags || []).join(' ')
        };

        var item = $(('<${tag} class="checkbox-field" tags="${tags}" checklist-index="${index}" ${hidden} ${disabled}>' +
                         '<input type="checkbox" value="${value}" checklist-index="${index}" ${disabled} ${checked}/>' +
                         '<div class="checkbox-label">' +
                             '<span class="checkbox-label-text" ${disabled}>${label}</span>' +
                             '<span class="checkbox-label-help" ${disabled}>${help}</span>' +
                         '</div>' +
                      '</${tag}>').template(context));

        var checkbox = $('input[type="checkbox"]', item);
        checkbox.data('checklist-item', {data: data, index:index});

        // this.updateItem(target, item, data, undefined, index);
        return item;
    },

    updateItem: function(target, item, data, previous, index, action)
    {
        if (action === 'select')
            return this.selectItem(target, item, data, previous, index);

        var value = this._getItemValue(data);
        var checkbox = $('input[type="checkbox"]', item);
        var disabled = data.disabled || this._disabled;

        checkbox.toggleAttr('disabled', data.disabled || disabled)
                .attr('value', value)
                .attr('checklist-index', index)
                .data('checklist-item', {data: data, index:index})

        checkbox.prop('checked', data.selected);

        $('.checkbox-label-text', item).toggleAttr('disabled', disabled)
                                       .html(data.label);

        $('.checkbox-label-help', item).toggleAttr('disabled', disabled)
                                       .html(data.help);

        item.toggleAttr('tags', data.tags, (data.tags || []).join(' '))
            .toggleClass('hidden', !data.visible)
            .toggleClass('disabled', disabled)
            .attr('checklist-index', index);
    },

    selectItem: function(target, item, data, previous, index) {
        $('input[type="checkbox"]', item).prop('checked', data.selected);
    },

    items: function(target) {
        return $('.checkbox-field', target).sort(function(a, b) {
            return parseInt($(a).attr('checklist-index')) - parseInt($(b).attr('checklist-index')); 
        });
    },

    converter: function(converter) {
        return Object.property(this, '_converter', converter);
    },

    parseItem: function(target, item, index)
    {
        var converter = this._converter;
        var input = $('input[type="checkbox"]', item);
        var label = $('.checkbox-label', item);
        var help = $('.checkbox-helptext', item);
        var value = input.attr('value');

        return {
            label:    label.html(), 
            value:    Object.isFunc(converter) ? converter(value) : value,
            disabled: input.is('[disabled]') || target.is('[disabled]'), 
            selected: input.is(':checked'),
            help:     help.html(),
            tags:     input.is('[tags]') ? input.attr('tags').split(' ') : [],
            visible:  true
        };
    },

    parse: function(target)
    {
        var self = this;

        this._itemtag = this.items(target).first().prop('tagName') || this._itemtag;

        return this.items(target).map(function(index) {
            return self.parseItem(target, $(this), index);
        }).get();
    }
});

creme.model.CheckGroupListRenderer = creme.model.CheckListRenderer.sub({
    _init_: function(options)
    {
        var options = $.extend({grouptag: 'ul'}, options || {});

        this._super_(creme.model.CheckListRenderer, '_init_', options);
        this._grouptag = options.grouptag;
    },

    insertGroup: function(target, before, groupname)
    {
        var group = $('.checkbox-group[label="' + groupname + '"]', target);

        if (group && group.length) {
            return group;
        }

        group = $(('<${tag} class="checkbox-group" label="${name}">' +
                   '   <li class="checkbox-group-header">${name}</li>' +
                   '</${tag}>').template({
                       tag: this._grouptag,
                       name: groupname
                   }));

        if (before && before.length) {
            before.parent().before(group);
        } else {
            target.append(group);
        }

        return group;
    },

    insertItem: function(target, before, data, index)
    {
        var group = target;
        var previous_groupname = before && before.length ? before.parent().attr('label') : undefined;
        var next_groupname = data.group;

        if (next_groupname) {
            group = this.insertGroup(target, before, next_groupname);
        }

        if (before && before.length)
        {
            if (next_groupname && previous_groupname !== next_groupname) {
                before = $('.checkbox-field:first', group);
            }

            before.before(this.createItem(target, before, data, index));
        } else {
            group.append(this.createItem(target, before, data, index));
        }
    },

    removeItem: function(target, item, data, index)
    {
        var group = data.group ? item.parent() : undefined;

        item.remove();

        if (group && this.items(group).length < 1)
            group.remove();
    },

    updateItem: function(target, item, data, previous, index, action)
    {
        if (action === 'select') {
            return this._super_(creme.model.CheckListRenderer, 'updateItem', target, item, data, previous, index, action);
        }

        var group = target;
        var prev_group = item.parent();

        var previous_groupname = previous ? previous.group : undefined;
        var next_groupname = data.group;

        if (next_groupname) {
            group = this.insertGroup(target, item.next(), next_groupname);
        }

        if (previous_groupname !== next_groupname)
        {
            item.remove();
            group.append(item);

            if (prev_group && (this.items(prev_group).length) < 1)
                prev_group.remove();
        }

        return this._super_(creme.model.CheckListRenderer, 'updateItem', target, item, data, previous, index, action);
    },

    parseItem: function(target, item, index)
    {
        var data = this._super_(creme.model.CheckListRenderer, 'parseItem', target, item, index);
        var checkbox_group = item.parent();

        data.group = (checkbox_group && checkbox_group.is('.checkbox-group')) ? option_group.attr('label') : undefined;
        return data;
    }
});

}(jQuery));
