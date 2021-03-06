
(function($) {
    "use strict";

    window.QUnitMixin = function() {
        var self = this;
        var reserved = ['setup', 'teardown', 'beforeEach', 'afterEach'];
        var mixins = this.__mixins = [QUnitBaseMixin].concat(Array.copy(arguments));

        mixins.forEach(function(mixin) {
            for (var key in mixin) {
                if (reserved.indexOf(key) === -1) {
                    self[key] = mixin[key];
                }
            }
        });
    };

    window.QUnit.skipIf = function(condition, name, callable) {
        var skipIt = Object.isFunc(condition) ? condition() : Boolean(condition);

        if (skipIt) {
            QUnit.skip(name, callable);
        } else {
            QUnit.test(name, callable);
        }
    };

    window.QUnit.browsers = {
        isChrome: function() {
            // headless chrome does not have window.chrome defined
            // (see https://github.com/ChromeDevTools/devtools-protocol/issues/83)
            return !!window.chrome || /HeadlessChrome/.test(window.navigator.userAgent);
        },
        isHeadless: function() {
            return Object.isNone(navigator.webdriver) === false;
        },
        isFirefox: function() {
            return 'MozAppearance' in document.documentElement.style;
        }
    };

    QUnitMixin.prototype = {
        beforeEach: function() {
            var self = this;

            this.__mixins.forEach(function(mixin) {
                if (Object.isFunc(mixin.beforeEach)) {
                    mixin.beforeEach.call(self);
                }
            });
        },

        afterEach: function(env) {
            var self = this;

            Array.copy(this.__mixins).reverse().forEach(function(mixin) {
                if (Object.isFunc(mixin.afterEach)) {
                    mixin.afterEach.call(self, env);
                }
            });
        }
    };

    window.QUnitBaseMixin = {
        beforeEach: function() {
            this.__qunitBodyElementCount = $('body').children().length;
            this.qunitFixture().attr('style', 'position: absolute;top: -10000px;left: -10000px;width: 1000px;height: 1000px;');
        },

        afterEach: function(env) {
            var count = $('body').children().length;

            if (this.__qunitBodyElementCount !== count) {
                throw Error('QUnit incomplete DOM cleanup (expected ${expected}, got ${count}) : ${test}\n${stack}'.template({
                       test: env.test.testName,
                       stack: env.test.stack,
                       expected: this.__qunitBodyElementCount,
                       count: count
                   }));
            }
        },

        qunitFixture: function(name) {
            var fixture = $('#qunit-fixture');

            if (fixture.size() === 0) {
                throw Error('Missing qunit-fixture element !');
            };

            if (name === undefined || name === null) {
                return fixture;
            }

            name = String(name);
            var subfixture = fixture.find('#qunit-fixture-' + name);

            if (subfixture.length === 0) {
                subfixture = $('<div id="qunit-fixture-' + name + '"></div>').appendTo(fixture);
            }

            return subfixture;
        },

        assertRaises: function(block, expected, message) {
            QUnit.assert.raises(block,
                   function(error) {
                        ok(error instanceof expected, 'error is ' + expected);
                        equal(message, '' + error);
                        return true;
                   });
        },

        assertNoXSS: function(block) {
            // Theses scripts are inspired by those found here:
            // https://owasp.org/www-community/xss-filter-evasion-cheatsheet
            var scripts = [
                '<script>QUnit.pushFailure("XSS < script>...< /script>");</script>',
                '<img src="javascript:QUnit.pushFailure(\'XSS < img src=...>\')" />',
                '<img src=/ onerror="QUnit.pushFailure(\'XSS < img onerror=...>\')"></img>',
                '\<a data-test="qunitXSS" onmouseover="QUnit.pushFailure(\'XSS < a mouseover=...>\')"\>xxs link\</a\>',
            ];

            scripts.forEach(function(script) {
                var success = false;

                try {
                    block.bind(this)(script);
                    success = true;
                } finally {
                    ok(success, 'XSS test as failed. See logs for stacktrace.');
                }

                // Trigger events for some XSS issues
                $('[data-test="qunitXSS"]').mouseover().click();
            }.bind(this));
        },

        equalHtml: function(expected, element, message) {
            QUnit.assert.equal($('<div>').append(expected).html(), $(element).html(), message);
        },

        equalOuterHtml: function(expected, element, message) {
            QUnit.assert.equal($('<div>').append(expected).html(), $('<div>').append($(element).clone()).html(), message);
        }
    };

    window.QUnitConsoleMixin = {
        beforeEach: function() {
            this.resetMockConsoleWarnCalls();

            var self = this;
            var __consoleWarn = this.__consoleWarn = console.warn;
            var __consoleError = this.__consoleError = console.error;

            console.warn = function() {
                var args = Array.copy(arguments);
                self.__consoleWarnCalls.push(args);
                return __consoleWarn.apply(this, args);
            };

            console.error = function() {
                var args = Array.copy(arguments);
                self.__consoleErrorCalls.push(args);
                return __consoleError.apply(this, args);
            };
        },

        afterEach: function() {
            console.warn = this.__consoleWarn;
            console.error = this.__consoleError;
        },

        mockConsoleWarnCalls: function() {
            return this.__consoleWarnCalls;
        },

        resetMockConsoleWarnCalls: function() {
            this.__consoleWarnCalls = [];
        },

        mockConsoleErrorCalls: function() {
            return this.__consoleWarnCalls;
        },

        resetMockConsoleErrorCalls: function() {
            this.__consoleWarnCalls = [];
        }
    };
}(jQuery));
