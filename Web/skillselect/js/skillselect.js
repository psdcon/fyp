
var skillselect = angular.module('skillselect', ['ngRoute','ngAnimate']);

// Configure our routes
skillselect.config(function($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl : 'pages/home.php',
      controller  : 'mainController'
    })

    .when('/videos', {
      templateUrl : 'pages/videos_list.php',
      controller  : 'videosController'
    })

    .when('/videos/:vidId', {
      templateUrl : function(params){
        return 'pages/video_details.php?video_id=' + params.vidId; },
        controller  : 'videoDetailsController'
    })

    .otherwise({
      templateUrl: 'pages/404.html'
    });

});

// Create the controller and inject Angular's $scope
skillselect.controller('mainController', function($scope) {
  // Nothing
});

skillselect.controller('videosController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

  // For changing page from code
  $scope.go = function ( path ) {
    $location.path( path );
  };
}]);

skillselect.controller('videoDetailsController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

  // Scroll to top because page may have been scrolled down in the list.
  scrollTo(0,0);

}]);
