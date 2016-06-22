/*
 * Copyright 2016 FUJITSU LIMITED
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */

'use strict';

angular
    .module('monitoring.directives', [
        'horizon.framework.widgets',
        'monitoring.filters',
        'monitoring.services',
        'gettext'
    ])
    .directive('monAlarmExpressions',
        ['monitoringApp.staticPath', monAlarmExpressionsDirective]
    )
    .directive('monAlarmExpression',
        ['monitoringApp.staticPath', monAlarmExpressionDirective]
    );

function monAlarmExpressionsDirective(staticPath){

    return {
        restrict: 'E',
        scope: {
            metrics: '=metrics',
            functions: '=functions',
            operators: '=operators',
            comparators: '=comparators',
            operators: '=operators',
            connectable: '=connectable'
        },
        templateUrl: staticPath + 'expression/compound_expression.tpl.html',
        controller: ['$q', '$scope', 'monExpressionBuilder', CompoundExpressionController],
        controllerAs: 'vm',
        bindToController: true
    }

    function CompoundExpressionController($q, $scope, monExpressionBuilder) {
        // private
        var vm = this;

        // scope
        vm.expression = '';
        vm.subExpressions = undefined;
        vm.matchBy = undefined;
        vm.deterministic = false;

        // api
        vm.touch = touch;
        vm.addExpression = addExpression;
        vm.removeExpression = removeExpression;
        vm.reorderExpression = reorderExpression;

        // listen
        $scope.$on('$destroy', destroy);

        // init
        $scope.$applyAsync(init);

        function addExpression($event, $index) {
            if($event){
                $event.preventDefault();
            }
            vm.subExpressions.push({
                fun: undefined,
                metric: undefined,
                cmp: undefined,
                threshold: 0,
                matchBy: [],
                deterministic: false,
                dimensions: [],
                preview: false,
                op: undefined
            });

            return true;
        }

        function removeExpression($event, index) {
            $event.preventDefault();
            vm.subExpressions.splice(index, 1);
            return true;
        }

        function reorderExpression($event, which, where) {
            $event.preventDefault();
            vm.subExpressions[where] = vm.subExpressions.splice(which, 1, vm.subExpressions[where])[0]
            return true;
        }

        function touch() {
            var matchBy = [],
                deterministic = true;

            angular.forEach(vm.subExpressions, function updater(expr, index){
                angular.forEach(expr.matchBy || [], function it(mb){
                    if(matchBy.indexOf(mb) < 0){
                        matchBy.push(mb);
                    }
                });
                deterministic = deterministic && expr.deterministic;
            });

            vm.deterministic = deterministic;
            vm.matchBy = matchBy = matchBy.sort();
            vm.expression = monExpressionBuilder.asString(vm.subExpressions);

            $scope.$emit('mon_match_by_changed', matchBy);
            $scope.$emit('mon_deterministic_changed', deterministic);

            return true;
        }

        function init() {
            if(vm.metrics.length) {
                vm.subExpressions = [];
                vm.matchBy = [];

                addExpression();
            }
        }

        function destroy() {
            delete vm.metrics;
            delete vm.expression;
            delete vm.subExpressions;
            delete vm.deterministic;
        }

    }

}

function monAlarmExpressionDirective(staticPath) {
    return {
        restrict: 'E',
        require: '^monAlarmExpressions',
        scope: {
            metrics: '=metrics',
            functions: '=functions',
            comparators: '=comparators',
            operators: '=operators',
            expression: '=subExpression',
            connectable: '=connectable',
            preview: '=preview'
        },
        templateUrl: staticPath + 'expression/expression.tpl.html',
        link: linkFn,
        controller: ['$q', '$scope', AlarmExpressionController],
        controllerAs: 'vm',
        bindToController: true
    }

    function linkFn(scope, el, attrs, monAlarmExpressions) {
        scope.$on('$destroy', (function(){

            var watcher = scope.$watch('vm.expression', function(expr, oldExpr) {
                if (expr !== oldExpr) {
                    monAlarmExpressions.touch(expr);
                }
            }, true);

            return function destroyer() {
                watcher();
            };

        }()));
    }

    function AlarmExpressionController($q, $scope) {
        var vm = this;

        // setup model
        vm.model = undefined;

        vm.tags = [];
        vm.matchingMetrics = [];
        vm.editing = false;

        // api
        vm.possibleDimensions = possibleDimensions;

        // listeners
        vm.updateExpression = updateExpression;
        vm.onMetricChanged = onMetricChanged;
        vm.onDimensionsUpdated = onDimensionsUpdated;
        vm.reset = resetExpression;

        // init
        $scope.$applyAsync(init);
        $scope.$on('$destroy', destroyer());

        function init() {
            vm.expression.metric = vm.metrics[0];
            vm.expression.fun = vm.functions[0][0];
            vm.expression.cmp = vm.comparators[0][0];

            onMetricChanged(vm.metrics[0]);
        }

        function destroyer() {

            var connectableWatcher = $scope.$watch('vm.connectable', function(nval, oval) {

                console.log(arguments);

                if (nval === oval) {
                    return false;
                }
                if(!nval) {
                    vm.expression.op = false;
                }
            });

            return function () {

                connectableWatcher();

                delete vm.tags;
                delete vm.matchingMetrics;
            }
        }

        function updateExpression() {
            var dim = [];
            var expressionArray;

            if (vm.tags.length > 0) {
                angular.forEach(vm.tags, function(value, key) {
                    dim.push(value['text']);
                });
                vm.expression.dimensions = dim;
            }
        }

        function resetExpression() {
            vm.matchingMetrics = [];
            vm.tags = [];
        }

        function possibleDimensions(query) {
            return $q(function(resolve, reject) {
                var dim = {}
                var dimList = []
                angular.forEach(vm.matchingMetrics, function(value, name) {
                    for (var key in value.dimensions) {
                        if (value.dimensions.hasOwnProperty(key)) {
                            var dimStr = key + "=" + value.dimensions[key]
                            if (dimStr.indexOf(query) === 0) {
                                dim[dimStr] = dimStr;
                            }
                        }
                    }
                });
                angular.forEach(dim, function(value, name) {
                    dimList.push(value);
                });
                resolve(dimList);
            });
        }

        function onDimensionsUpdated() {
            onMetricChanged(vm.expression.metric);
        }

        function onMetricChanged(metric) {
            var mm = [];
            var uniqueDimensionKeys = [];
            var tags = vm.tags || [];

            angular.forEach(vm.metrics, function(value, key) {
                if (value.name === metric.name) {
                    var match = true;
                    for (var i = 0; i < tags.length; i++) {
                        var vals = tags[i]['text'].split('=');
                        if (value.dimensions[vals[0]] !== vals[1]) {
                            match = false;
                            break;
                        }

                    }
                    if (match) {
                        mm.push(value)
                    }
                }
            });

            angular.forEach(mm, function(value, key){
                angular.forEach(value.dimensions, function(value, key){
                    if(uniqueDimensionKeys.indexOf(key) < 0){
                        uniqueDimensionKeys.push(key);
                    }
                });
            });

            uniqueDimensionKeys.sort();

            vm.matchingMetrics = mm
            vm.uniqueDimensionKeys = vm.expression.matchBy = uniqueDimensionKeys;

            updateExpression();
        }

    }

}
