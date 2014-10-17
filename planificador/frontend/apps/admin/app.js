function router($routeProvider) {
    $routeProvider
        .when('/', {
            templateUrl: 'index.html',
            controller: 'AdminCtrl as vm'
        })
        .when('/test1', {
            templateUrl: 't1.html',
            controller: 'AdminCtrl as vm'
        })
        .when('/test2', {
            templateUrl: 't2.html',
            controller: 'AdminCtrl as vm'
        })
        .when('/test3', {
            templateUrl: 't3.html',
            controller: 'AdminCtrl as vm'
        })
        .when('/test4', {
            templateUrl: 't4.html',
            controller: 'AdminCtrl as vm'
        })
        .otherwise({
            redirectTo: '/'
        });
}


angular.module('adminApp', ['ngRoute'])
    .config(function($interpolateProvider, $httpProvider) {
        $interpolateProvider.startSymbol('[[').endSymbol(']]');
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.headers.post['Content-Type'] = 'application/x-www-form-urlencoded;charset=utf-8';
    })
    .config(router);