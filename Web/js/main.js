
var fyp = angular.module('fyp', ['ngRoute','ngAnimate']);

// Configure our routes
fyp.config(function($routeProvider) {
  $routeProvider
    .when('/', {
      templateUrl : 'pages/home.php',
      controller  : 'mainController'
    })

    .when('/videos', {
      templateUrl : 'pages/list_videos.php',
      controller  : 'videosListController'
    })

    .when('/label/:vidId', {
      templateUrl : function(params){
        return 'pages/label_video.php?video_id=' + params.vidId; },
        controller  : 'labelVideoController'
    })

    .when('/judge/:vidId', {
      templateUrl : function(params){
        return 'pages/judge_video.php?video_id=' + params.vidId; },
        controller  : 'judgeVideoController'
    })

    .otherwise({
      templateUrl: 'pages/404.html'
    });

});

// Create the controller and inject Angular's $scope
fyp.controller('mainController', function($scope) {

});

fyp.controller('videosListController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

}]);

fyp.controller('labelVideoController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

}]);

fyp.controller('judgeController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

}]);

fyp.controller('judgeVideoController', ['$scope', '$routeParams', '$location', function($scope, $routeParams, $location){

}]);
