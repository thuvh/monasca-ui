'use strict';
angular.module('monitoring.controllers', [])
    .controller('monitoringController', function ($scope, $http, $timeout, $location) {
         $scope.fetchStatus = function() {
            $http({method: 'GET', url: $location.absUrl().concat('status')}).
                success(function(data, status, headers, config) {
                  // this callback will be called asynchronously
                  // when the response is available
                    var i;
                    for (i=0; i < data.series.length; i++) {
                        var group = data.series[i]
                        for (var j in group.services) {
                            var service = group.services[j]
                            service['icon'] = getIcon(service['class'])
                        }
                    }
                    $scope._serviceModel = data.series
               }).
                error(function(data, status, headers, config) {
                    $scope.stop();
                });
        }
        $scope.onTimeout = function(){
            mytimeout = $timeout($scope.onTimeout,10000);
            $scope.fetchStatus()
        }
        var mytimeout = $timeout($scope.onTimeout,10000);

        $scope.stop = function(){
            $timeout.cancel(mytimeout);
        }
    })
    .controller('alarmEditController', function ($scope, $http, $timeout, $q) {
        $scope.metrics = metricsList;
        $scope.metricNames = uniqueNames(metricsList, 'name')
        $scope.currentMetric = $scope.metricNames[0];
        $scope.currentFunction = "max";
        $scope.currentComparator = ">";
        $scope.currentThreshold = 0;
        $scope.matchingMetrics= [];
        $scope.tags = [];
        $scope.possibleDimensions = function(query) {
            var deferred = $q.defer();
            var dim = {}
            var dimList = []
            angular.forEach($scope.matchingMetrics, function(value, name) {
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
                dimList.push(value)
            });
            deferred.resolve(dimList);
            return deferred.promise;
        };
        $scope.metricChanged = function() {
            if ($scope.defaultTag.length > 0) {
                $scope.tags = [{text: $scope.defaultTag}];
            }
            $scope.saveDimension();
        }
        $scope.saveExpression = function() {
            $('#dimension').val($scope.formatDimension());
        }
        $scope.saveDimension = function() {
            $scope.saveExpression();

            var mm = []
            angular.forEach($scope.metrics, function(value, key) {
                if (value.name === $scope.currentMetric) {
                    var match = true;
                    for (var i = 0; i < $scope.tags.length; i++) {
                        var vals = $scope.tags[i]['text'].split('=');
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
            $scope.matchingMetrics = mm
            $scope.dimnames = ['name', 'dimensions'];
            $('#match').val($scope.formatMatchBy());
        }
        $scope.formatDimension = function() {
            var dim = ''
            angular.forEach($scope.tags, function(value, key) {
                if (dim.length) {
                    dim += ','
                }
                dim += value['text']
            })
            return $scope.currentFunction + '(' + $scope.currentMetric + '{' + dim + '}) ' + $scope.currentComparator + ' ' + $scope.currentThreshold;
        }
        $scope.formatMatchBy = function() {
            var dimNames = {}
            for (var i = 0; i < $scope.matchingMetrics.length; i++) {
                for (var attrname in $scope.matchingMetrics[i].dimensions) { dimNames[attrname] = true; }
            }
            var matches = [];
            for (var attrname in dimNames) { matches.push(attrname); }
            return matches;
        }
        $scope.init = function(defaultTag) {
            if (defaultTag.length > 0) {
                $scope.tags = [{text: defaultTag}];
            }
            $scope.defaultTag = defaultTag;
            $scope.saveDimension();
        }
    })
    .controller('alarmNotificationFieldController', NotificationField);

    function NotificationField(){

        var vm = this;
        var allOptions = {};

        vm.empty = true;
        vm.list = [];
        vm.select = {
            model:null,
            options:[]
        };


        vm.init = function(data){
            data = JSON.parse(data);
            vm.empty = data.length === 0;
            data.forEach(prepareNotify);
        };
        vm.add = function(){
            if(vm.select.model){
                vm.list.push(allOptions[vm.select.model]);

                removeFromSelect();
                vm.select.model = null;
            }
        };
        vm.remove = function(id){
            for(var i = 0;i<vm.list.length;i+=1){
                if(vm.list[i].id === id){
                    vm.list.splice(i, 1);
                    vm.select.options.push(allOptions[id]);
                    break;
                }
            }
            vm.select.model = null;
        };

        function prepareNotify(item){
            var selected = item[4]
            var notify = {
                id: item[0],
                label: item[1] +' ('+ item[2] +')',
                name: item[1],
                type: item[2],
                address: item[3]
            };
            allOptions[notify.id] = notify;
            if(selected){
                vm.list.push(notify);
            } else {
                vm.select.options.push(notify);
            }
        }

        function removeFromSelect(){
             var opts = vm.select.options;
             for(var i = 0;i<opts.length;i+=1){
                if(opts[i].id === vm.select.model){
                    opts.splice(i, 1);
                    break;
                }
             }
        }
    }

angular.module('monitoring.filters', [])
    .filter('spacedim', function () {
        return function(text) {
            if (typeof text == "string")
                return text;
            return JSON.stringify(text).split(',').join(', ');
        }
    })


function uniqueNames(input, key) {
    var unique = {};
    var uniqueList = [];
    for(var i = 0; i < input.length; i++){
        if(typeof unique[input[i][key]] == "undefined"){
            unique[input[i][key]] = "";
            uniqueList.push(input[i][key]);
        }
    }
    return uniqueList.sort();
}

function getIcon(status) {
    if (status === 'chicklet-error')
        return '/static/monitoring/img/critical-icon.png'
    else if (status === 'chicklet-warning')
        return '/static/monitoring/img/warning-icon.png'
    else if (status === 'chicklet-unknown')
        return '/static/monitoring/img/unknown-icon.png'
    else if (status === 'chicklet-success')
        return '/static/monitoring/img/ok-icon.png'
    else if (status === 'chicklet-notfound')
        return '/static/monitoring/img/notfound-icon.png'
}
