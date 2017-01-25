angular.module('anatomy.tagging', [
  'anatomy.tagging.controllers',
  'anatomy.tagging.directives',
  'anatomy.tagging.services',
  'anatomy.tagging.filters',
  'ngCookies', 
  'ngRoute',
  'slugifier',
  'ui.bootstrap', 
  'angular-svg-round-progress',
  'ui.tree',
])

.config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
  $routeProvider.when('/', {
    controller : 'ImageListController',
    templateUrl : 'static/tpl/image_list_tpl.html'
  }).when('/home', {
    controller : 'ImageListController',
    templateUrl : 'static/tpl/homepage_tpl.html'
  }).when('/home/:section?', {
    controller : 'ImageListController',
    templateUrl : 'static/tpl/section_tpl.html'
  }).when('/image/:image', {
    controller : 'ImageController',
    templateUrl : 'static/tpl/image_tpl.html'
  }).when('/practice/:image', {
    controller : 'PracticeController',
    templateUrl : 'static/tpl/practice_tpl.html'
  }).when('/terms/:image?', {
    controller : 'TermsController',
    templateUrl : 'static/tpl/terms_tpl.html'
  }).when('/relations/export', {
    controller : 'RelationsExportController',
    templateUrl : 'static/tpl/relations_export_tpl.html'
  }).when('/relations/tree/:type?', {
    controller : 'RelationsTreeController',
    templateUrl : 'static/tpl/relations_tree_tpl.html'
  }).when('/relations/:source?', {
    controller : 'RelationsController',
    templateUrl : 'static/tpl/relations_tpl.html'
  }).otherwise({
    //redirectTo : '/'
  });

  $locationProvider.html5Mode(true);

}])

.filter('startFrom', function() {
  return function(input, start) {
    start = +start; //parse to int
    return input && input.slice(start);
  };
});

