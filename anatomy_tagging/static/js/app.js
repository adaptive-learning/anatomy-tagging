angular.module('anatomy.tagging', [
  'anatomy.tagging.controllers',
  'anatomy.tagging.directives',
  'anatomy.tagging.services',
  'ngCookies', 
  'ngRoute',
  'slugifier',
  'ui.bootstrap', 
])

.config(['$routeProvider', '$locationProvider',
    function($routeProvider, $locationProvider) {
  $routeProvider.when('/', {
    controller : 'ImageListController',
    templateUrl : 'static/tpl/image_list_tpl.html'
  }).when('/image/:image', {
    controller : 'ImageController',
    templateUrl : 'static/tpl/image_tpl.html'
  }).when('/terms/:image?', {
    controller : 'TermsController',
    templateUrl : 'static/tpl/terms_tpl.html'
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
