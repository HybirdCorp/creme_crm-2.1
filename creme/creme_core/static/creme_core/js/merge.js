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

/*
 * Requires : jQuery lib, creme.utils
 */

creme.merge = creme.merge || {};

creme.merge.selectOtherEntityNRedirect = function(model_id) {
    var url = '/creme_core/entity/merge/select_other/' + model_id;
    var action = creme.lv_widget.listViewAction(url, {multiple:false});

    action.onDone(function(event, data) {
        window.location.href = '/creme_core/entity/merge/' + model_id + ',' + data[0];
    });

    return action.start();
}
