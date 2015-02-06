angular.module('anatomy.tagging', [
  'anatomy.tagging.controllers',
  'anatomy.tagging.directives',
  'anatomy.tagging.services',
  'ngCookies', 
  'ngRoute',
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
  }).otherwise({
    //redirectTo : '/'
  });

  $locationProvider.html5Mode(true);

}]);
