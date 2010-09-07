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

//(function() {
//    var old_Raphael = Raphael;
//    Raphael = function() {
//        var raphael = old_Raphael.apply(this, arguments);
//        var old_set = raphael.set;
//        raphael.set = function() {
//            var set = old_set.apply(this, arguments);
//            set.toString = function () { return 'Object'; };
//            return set;
//        };
//        return raphael;
//    };
//})();

creme.graphael = {};

creme.graphael._init = function(selector)
{
    var nodes = $(selector);
    for(var i=-1, l=nodes.length; ++i < l;)
    {
        var node = nodes[i];
        var $node = $(node);
        
        var n_width  = $node.width();
        var n_height = n_width * 0.5;

        var r = Raphael(node, n_width, n_height);
        $node.data('graphael', r);
    }
    return nodes;
};

creme.graphael.init = function(selector)
{
    var initial_nodes = $(selector);
    var nodes = initial_nodes.not('.initialized');

    for(var i=-1, l=nodes.length; ++i < l;)
    {
        var node = nodes[i];
        var $node = $(node);
        //Not really optimized because _init takes a selector and not a node
        creme.graphael._init(node);
        $node.addClass('initialized');
    }
    return initial_nodes;
};

creme.graphael.paddings = {
    'L_PAD': 15,//left padding
    'R_PAD': 15,//right padding
    'H_PAD': 15,//top padding
    'B_PAD': 15,//bottom padding
    'I_PAD': 4,//Inter elements padding not an apple thing ;)
    'CUR_Y': 10
}

creme.graphael.barchart = {};

creme.graphael.barchart.fin = function (r, chart){
    //var dims = chart.bar.getBBox();
    chart.flag = r.g.popup(chart.bar.x, chart.bar.y + creme.graphael.paddings.I_PAD, chart.bar.value || "0").insertBefore(chart);
};

creme.graphael.barchart.fout = function () {
    this.flag.animate({opacity: 0}, 300, function () {this.remove();});
};

creme.graphael.simple_barchart = function(options)
{
    if(!options || options == undefined || options.instance==undefined) return;//Need at least a Raphael's instance
    var graphael = options.instance;
    var paddings = $.extend(creme.graphael.paddings, options.paddings);
    var x = options.x || [], y = options.y || [];

    var lpad = paddings.L_PAD;
    var hpad = paddings.H_PAD;
    var ipad = paddings.I_PAD;


    var barchart = graphael.g.barchart(lpad, hpad/2, graphael.width-lpad, graphael.height-hpad, [y])
                    .hover(function(e){creme.graphael.barchart.fin(graphael, this)}, creme.graphael.barchart.fout);

    var show_legend = false ? (options.show_legend == undefined || options.show_legend == false) : true;
    if(!show_legend ||  x.length <=5)
    {
        barchart.label([x], true);
    }
    else
    {
        barchart.label([creme.utils.range(1, x.length+1)], true);
    }

    var lbl_ordinate = graphael.g.text(barchart.getBBox().x/2+lpad , graphael.height/2, options.ordinate_lbl || "").rotate(270);
    var lbl_abscissa = graphael.g.text(graphael.width/2, graphael.height - ipad, options.abscissa_lbl || "");

    if(options.gen_date_selector)
    {
        $(options.gen_date_selector).text(new Date().toString("dd-MM-yyyy HH:mm"));//Needs Datejs but doesn't bug when not
    }
};

//TODO: Do me more generic ? Permit more than 2 curves ? Why a json option object doesn't work ???
// Rename variables
creme.graphael._init_evolution_graph = function (targetNodeId, x1, y1, y2)
{
    var table = $('#'+targetNodeId);

    var t_width = table.width();
    var t_height = t_width * 0.35;

    var L_PAD = 15;//left padding
    var R_PAD = 15;//right padding
    var H_PAD = 10;//top padding
    var B_PAD = 10;//bottom padding
    var I_PAD = 4;//Inter elements padding not an apple thing ;)
    var CUR_Y = H_PAD;
    var paid_color = '#a2bf2f';
    var promise_color = '#94C6DB';

    //var r = Raphael(table[0], t_width, t_height);
    var r = Raphael(targetNodeId, t_width, t_height);

    var c_paid      = r.circle(L_PAD, CUR_Y, 5).attr({fill: paid_color, stroke: "#fff", "stroke-width": 1});
    var lbl_paid    = r.g.text(0, 0, "Sommes effectivement versées");
    lbl_paid.attr({
        x : c_paid.getBBox().x + lbl_paid.getBBox().width/2 + 4*I_PAD,
        y : c_paid.getBBox().y + c_paid.getBBox().height/2
    });

    var c_promise   = r.circle(lbl_paid.getBBox().x + lbl_paid.getBBox().width + 4*I_PAD , CUR_Y, 5).attr({fill: promise_color, stroke: "#fff", "stroke-width": 1});
    var lbl_promise = r.g.text(0 , 0, "Sommes promises");
    lbl_promise.attr({
        x : c_promise.getBBox().x + lbl_promise.getBBox().width/2 + 4*I_PAD,
        y : c_promise.getBBox().y + c_promise.getBBox().height/2
    });

    CUR_Y += lbl_promise.getBBox().y;

    var lines = r.g.linechart((t_width*0.15)/2, CUR_Y, t_width*0.85, t_height-CUR_Y-B_PAD, [x1,x1], [y1, y2], {nostroke: false, axis: "0 0 1 1", symbol: "o", shade:true, smooth: false, gutter:15, axisxstep:x1.length, colors : [paid_color,promise_color]}).hoverColumn(function () {
            this.tags = r.set();
            for (var i = 0, ii = this.y.length; i < ii; i++) {
                this.tags.push(r.g.tag(this.x, this.y[i], this.values[i], 160, 10).insertBefore(this).attr([{fill: "#fff"}, {fill: this.symbols[i].attr("fill")}]));
            }
        }, function () {
            this.tags && this.tags.remove();
        });
    lines.symbols.attr({r: 3});

    var lbl_sum = r.g.text(0 , 0, "Somme");
    lbl_sum.rotate(270);
    lbl_sum.attr({
        x : c_paid.getBBox().x,
        y : lines.getBBox().height/2
    });

    var lbl_year = r.g.text(0 , 0, "Année");
    lbl_year.attr({
        x : lines.getBBox().x + lines.getBBox().width/2,
        y : lines.getBBox().y + lines.getBBox().height + 4*I_PAD
    });
};


