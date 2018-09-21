(function($) {

var MOCK_PLOT_CONTENT_JSON_INVALID = '{"options": {, "data":[]}';
var MOCK_PLOT_CONTENT_JSON_EMPTY_DATA = '{"options": {}, "data":[]}';
var MOCK_PLOT_CONTENT_JSON_DEFAULT = '{"options": {}, "data":[[[1, 2],[3, 4],[5, 12]]]}';
var MOCK_PLOT_CONTENT_DEFAULT = {options: {}, data: [[[1, 2],[3, 4],[5, 12]]]};

QUnit.module("creme.widget.plot.js", new QUnitMixin(QUnitAjaxMixin, QUnitPlotMixin, QUnitWidgetMixin, {
    buildMockBackend: function() {
        return new creme.ajax.MockAjaxBackend({sync:true, name: 'creme.widget.plot.js'});
    },

    beforeEach: function() {
        this.resetMockPlotEvents();
        this.resetMockPlots();

        creme.utils.converters.register('mockPlotData', 'jqplotData', this._mockPlotData_to_jqplotData);
        creme.utils.converters.register('jqplotData', 'mockRendererData', this._jqplotData_to_mockRendererData);
    },

    afterEach: function() {
        this.resetMockPlotEvents();
        this.resetMockPlots();

        this.cleanupMockPlots();

        creme.utils.converters.unregister('mockPlotData', 'jqplotData');
        creme.utils.converters.unregister('jqplotData', 'mockRendererData');

        $('.ui-dialog-content').dialog('destroy');
        creme.widget.shutdown($('body'));
    },

    _mockPlotData_to_jqplotData: function(data) {
        var result = [];

        for(var s_index = 0; s_index < data.length; ++s_index) {
            var serie = data[s_index];
            var s_result = [];

            for(var index = 0; index < serie.length; ++index) {
                var entry = serie[index];
                
                if (entry) {
                    entry = [index + 1].concat(entry);
                } else {
                    entry = [index + 1];
                }

                s_result.push(entry);
            }

            result.push(s_result);
        }

        return result;
    },

    _jqplotData_to_mockRendererData: function(data) {
        var result = [];

        for(var s_index = 0; s_index < data.length; ++s_index) {
            var serie = data[s_index];
            var s_result = [];

            for(var index = 0; index < serie.length; ++index) {
                var entry = serie[index];

                if (entry && entry.length > 1) {
                    entry = [entry[1], entry[0]].concat(entry.slice(2));
                }

                s_result.push(entry);
            }

            result.push(s_result);
        }

        return result;
    },

    resetMockPlots: function() {
        this.plotContainer = $('#mock_creme_widget_plot_container');

        if (!this.plotContainer.get(0)) {
            $('body').append($('<div>').attr('id', 'mock_creme_widget_plot_container')
                                       .css('display', 'none'));
        }

        this.plotContainer = $('#mock_creme_widget_plot_container');
        this.mockPlots = [];
    },

    cleanupMockPlots: function() {
        for(var index = 0; index < this.mockPlots.length; ++index)
        {
            var plot = this.mockPlots[index];

            plot.remove();
            plot.unbind('plotSuccess');
            plot.unbind('plotError');
        }

        this.mockPlots = [];
    },

    createMockPlot: function(data, plotmode, savable, noauto)  {
        var options = {
                         plotmode: plotmode || 'svg', 
                         savable: savable || false
                      };

        var plot = creme.widget.buildTag($('<div/>'), 'ui-creme-jqueryplot', options, !noauto)
                               .append($('<script type="text/json">' + data + '</script>'));

        this.plotContainer.append(plot);
        this.mockPlots.push(plot);

        this.bindMockPlotEvents(plot);
        return plot;
    }
}));

QUnit.test('creme.widget.Plot.create (empty)', function(assert) {
    var element = this.createMockPlot('');

    creme.widget.create(element);
    this.assertReady(element);
    this.assertNoPlot(this, element, 'null');
});

QUnit.test('creme.widget.Plot.create (invalid)', function(assert) {
    var element = this.createMockPlot(MOCK_PLOT_CONTENT_JSON_INVALID);

    creme.widget.create(element);
    this.assertReady(element);
    this.assertNoPlot(this, element);

    equal(this.plotError.message.substr(0, 'JSON parse error'.length), 'JSON parse error');
});

QUnit.test('creme.widget.Plot.create (valid)', function(assert) {
    var element = this.createMockPlot(MOCK_PLOT_CONTENT_JSON_DEFAULT);

    stop(1);

    creme.widget.create(element, {}, function() {
        start();
    }, function() {
        start();
    });

    this.assertReady(element);
    this.assertPlot(this, element);
});

QUnit.test('creme.widget.Plot.draw (empty)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);

    this.assertReady(element);
    this.assertNoPlot(this, element, 'null');

    this.resetMockPlotEvents();
    stop(1);

    widget.draw(MOCK_PLOT_CONTENT_JSON_EMPTY_DATA, function() {
        start();
    }, function() {
        start();
    });

    this.assertReady(element);
    this.assertNoPlot(this, element, 'null');
});

QUnit.test('creme.widget.Plot.draw (valid)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    this.resetMockPlotEvents();
    stop(1);

    widget.draw(MOCK_PLOT_CONTENT_JSON_DEFAULT, function() {
        start();
    }, function() {
        start();
    });

    this.assertReady(element);
    this.assertPlot(this, element);
});

QUnit.test('creme.widget.Plot.draw (invalid)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    this.resetMockPlotEvents();
    stop(1);

    widget.draw(MOCK_PLOT_CONTENT_JSON_INVALID, undefined, function() {
        start();
    });

    this.assertReady(element);
    this.assertNoPlot(this, element);
    equal(this.plotError.message.substr(0, 'JSON parse error'.length), 'JSON parse error');
});

QUnit.test('creme.widget.Plot.redraw (valid, data)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    widget.plotData([[[1, 2],[3, 4],[5, 12]]]);

    deepEqual(widget.plotData(), [[[1, 2],[3, 4],[5, 12]]]);
    deepEqual(widget.plotOptions(), {});

    this.resetMockPlotEvents();
    stop(1);

    widget.redraw(function() {
        start();
    },
    function() {
        start();
    });

    this.assertPlot(this, element);
});


QUnit.test('creme.widget.Plot.redraw (empty, valid default)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertReady(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    widget.plotOptions({dataDefaults: [[[5, 2],[4, 4]]]});

    this.resetMockPlotEvents();
    stop(1);

    widget.redraw(function() {
        start();
    },
    function() {
        start();
    });

    this.assertPlot(this, element);
    deepEqual(widget.plotData(), []);
});


QUnit.test('creme.widget.Plot.redraw (valid, options)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {
                showDataLabels: true
            }
        }
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 2],[3, 4],[5, 12]]]);

    deepEqual(widget.plotData(), [[[1, 2],[3, 4],[5, 12]]]);
    deepEqual(widget.plotOptions(), plot_options);

    this.resetMockPlotEvents();
    stop(1);

    widget.redraw(function() {
        start();
    });

    this.assertPlot(this, element);
});

QUnit.test('creme.widget.Plot.preprocess (convert data)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        dataFormat: "mockPlotData"
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 2.58],[3, 40.5],[5, 121.78]]]);

    deepEqual(widget.plotData(), [[[1, 1, 2.58],[2, 3, 40.5],[3, 5, 121.78]]]);
    deepEqual(widget.plotOptions(), plot_options);
});

QUnit.test('creme.widget.Plot.preprocess (preprocess data)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        dataPreprocessors: ["swap"]
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 150.5, "a"],[2, 3.45, "b"],[3, 12.80, "c"]]]);
    widget.preprocess();

    var built_plot_options = {
        seriesDefaults: {
            renderer: $.jqplot.PieRenderer, 
            rendererOptions: {showDataLabels: true}
        },
        handlers: [],
        dataPreprocessors: ["swap"]
    };

    deepEqual(widget.plotInfo().built.data, [[[150.5, 1, "a"],[3.45, 2, "b"],[12.80, 3, "c"]]]);
    deepEqual(widget.plotInfo().built.options, built_plot_options);
});

QUnit.test('creme.widget.Plot.preprocess (preprocess data chained)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        dataPreprocessors: [
                            "swap", 
                            "tee"
                           ]
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 150.5, "a"],[2, 3.45, "b"],[3, 12.80, "c"]]]);
    widget.preprocess();

    var built_plot_options = {
        seriesDefaults: {
            renderer: $.jqplot.PieRenderer, 
            rendererOptions: {showDataLabels: true}
        },
        handlers: [],
        dataPreprocessors: ["swap", "tee"]
    };

    deepEqual(widget.plotInfo().built.data, [[[150.5, 1, "a"]],[[3.45, 2, "b"]],[[12.80, 3, "c"]]]);
    deepEqual(widget.plotInfo().built.options, built_plot_options);
});

QUnit.test('creme.widget.Plot.preprocess (convert + preprocess data)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        dataFormat: "mockPlotData",
        dataPreprocessors: ["swap"]
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[150.5, "a"],[3.45, "b"],[12.80, "c"]]]);
    widget.preprocess();

    var built_plot_options = {
        seriesDefaults: {
            renderer: $.jqplot.PieRenderer, 
            rendererOptions: {showDataLabels: true}
        },
        handlers: [],
        dataFormat: "mockPlotData",
        dataPreprocessors: ["swap"]
    };

    deepEqual(widget.plotInfo().built.data, [[[150.5, 1, "a"],[3.45, 2, "b"],[12.80, 3, "c"]]]);
    deepEqual(widget.plotInfo().built.options, built_plot_options);
});

QUnit.test('creme.widget.Plot.preprocess (preprocess options)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        series: 'preprocess.seriesLabel',
        seriesLabelOptions: {
            defaults: {showLabel: true},
            labelIndex: -1
        },
        axes: {
            xaxis: {
                ticks: 'preprocess.ticksLabel',
                ticksLabelOptions: {
                    labelIndex: 2,
                    seriesIndex: 0
                }
            }
        }
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 150.5, "a", "serie1"],[2,  3.45, "b"],[3, 12.80, "c"]],
                     [[1,  12.5, "serie2"],     [2, 13.45],     [3, 52.80]]]);

    deepEqual(widget.plotData(), [[[1, 150.5, "a", "serie1"],[2,  3.45, "b"],[3, 12.80, "c"]],
                                  [[1,  12.5, "serie2"],     [2, 13.45],     [3, 52.80]]]);
    deepEqual(widget.plotOptions(), plot_options);
    deepEqual(widget.plotInfo().built, undefined);

    widget.preprocess();

    var plot_built_options = {
        seriesDefaults: {
            renderer: $.jqplot.PieRenderer,
            rendererOptions: {showDataLabels: true}
        },
        series: [
            {
                showLabel: true,
                label: 'serie1'
            },
            {
                showLabel: true,
                label: 'serie2'
            }
        ],
        handlers: [],
        axes: {
            xaxis: {
                ticks: ["a", "b", "c"]
            }
        }
    };

    deepEqual(widget.plotInfo().built.options, plot_built_options);
    deepEqual(widget.plotData(), [[[1, 150.5, "a", "serie1"],[2,  3.45, "b"],[3, 12.80, "c"]],
                                  [[1,  12.5, "serie2"],     [2, 13.45],     [3, 52.80]]]);
    deepEqual(widget.plotOptions(), plot_options);
});

QUnit.test('creme.widget.Plot.preprocess (preprocess handlers)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        handlers: [
            {action: 'popup', event: 'click', url: '/mock/action/%d'},
            {action: 'redirect', event: 'dblclick', url: '/mock/action/%d'}
        ]
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 2.58],[3, 40.5],[5, 121.78]]]);

    deepEqual(widget.plotData(), [[[1, 2.58],[3, 40.5],[5, 121.78]]]);
    deepEqual(widget.plotOptions(), plot_options);

    widget.preprocess();

    var plot_built_options = {
        seriesDefaults: {
            renderer: $.jqplot.PieRenderer,
            rendererOptions: {showDataLabels: true}
        },
        handlers: [
            {action: creme.widget.PlotEventHandlers.get('popup'),    event: 'jqplotDataClick',    url: '/mock/action/%d'},
            {action: creme.widget.PlotEventHandlers.get('redirect'), event: 'jqplotDataDblclick', url: '/mock/action/%d'}
        ]
    };

    deepEqual(widget.plotInfo().built.options, plot_built_options);
});

QUnit.test('creme.widget.Plot.preprocess (preprocess invalid handler)', function(assert) {
    var element = this.createMockPlot('');
    var widget = creme.widget.create(element);
    this.assertActive(element);

    deepEqual(widget.plotData(), []);
    deepEqual(widget.plotOptions(), {});

    var plot_options = {
        seriesDefaults: {
            renderer: 'jqplot.PieRenderer', 
            rendererOptions: {showDataLabels: true}
        },
        handlers: [
            {action: 'popup', event: 'click', url: '/mock/action/%d'},
            {action: 'unknown', event: 'dblclick', url: '/mock/action/%d'}
        ]
    };

    widget.plotOptions(plot_options);
    widget.plotData([[[1, 2.58],[3, 40.5],[5, 121.78]]]);

    deepEqual(widget.plotData(), [[[1, 2.58],[3, 40.5],[5, 121.78]]]);
    deepEqual(widget.plotOptions(), plot_options);

    widget.redraw();

    this.assertNoPlot(this, element, 'Error: no such plot event handler "unknown"');
});

}(jQuery));
