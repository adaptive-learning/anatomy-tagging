angular.module('anatomy.tagging.controllers', [])

.controller('anatomyMain', function($scope) {
})

.controller('ImageListController', function($scope, imageService) {
  $scope.loading = true;

  imageService.all(true).success(function(data) {
    $scope.images = data.images;
    $scope.loading = false;

    imageService.all().success(function(data) {
      $scope.images = data.images;
    });
  });
})

.controller('ImageController', function($scope, imageService, termsService, colorService) {
  $scope.pathsByColor = {};
  $scope.loading = true;
  $scope.alerts = [];

  termsService.get().success(function(data) {
    $scope.terms = data;
  });

  imageService.get().success(function(data){
    $scope.image = data.image;
    $scope.paths = data.paths;
    for (var i = 0; i < data.paths.length; i++) {
      var p = data.paths[i];
      var c = p.color;
      if ((colorService.isGray(p.color) || p.color === 'none') && 
          (!p.term || p.term.code === 'no-practice')) {
        c = 'gray';
        if (!p.term) {
          $scope.setNoPractice(p);
        }
      }
      if (!$scope.pathsByColor[c]) {
        $scope.pathsByColor[c] = {
          paths : [],
          term : '',
        };
      }
      $scope.pathsByColor[c].paths.push(p);
      if ($scope.pathsByColor[c].term && $scope.pathsByColor[c].term.code && 
          (!p.term || $scope.pathsByColor[c].term.code != p.term.code)) {
        $scope.pathsByColor[c].showDetails = true;
        $scope.pathsByColor[c].term = null;
        $scope.pathsByColor[c].disabled = false;
      }
      if ($scope.pathsByColor[c].term !== null) {
        $scope.pathsByColor[c].term = p.term;
        if ($scope.pathsByColor[c].term && 
          $scope.pathsByColor[c].term.code === 'no-practice') {
        $scope.pathsByColor[c].disabled = true;
        }
      }
      if (p.term && p.term.code === "no-practice") {
        p.disabled = true;
      }
      //p.color = colorService.toGrayScale(p.color);
    }
    $scope.loading = false;
    imageService.save($scope.image, $scope.paths);
  });

  $scope.setNoPractice = function(path) {
      if (path.term && path.term.code && path.term.code === 'no-practice') {
        path.term = null;
        path.disabled = false;
      } else {
        path.term = {
          code : 'no-practice',
          name_la : 'Vyřazeno z procvičování'
        };
        path.disabled = true;
      }
      if (path.paths) {
        $scope.termUpdated(path);
      }
  };

  $scope.showDetails = function(byColor) {
    byColor.showDetails = !byColor.showDetails;
    $scope.updateFocused();
  };

  $scope.updateFocused = function() {
    if ($scope.focused && $scope.focused.paths) {
      $scope.termUpdated($scope.focused);
    }
  };

  $scope.focus = function(byColor) {
    $scope.updateFocused();
    $scope.focused = byColor;
    imageService.focus(byColor);
  };

  $scope.termUpdated = function(byColor) {
    for (var i = 0; i < byColor.paths.length; i++) {
      byColor.paths[i].term = byColor.term;
      byColor.paths[i].disabled = byColor.term && byColor.term.code === 'no-practice';
    }
  };

  $scope.notTooSmall= function(path) {
    return !path.isTooSmall;
  };

  $scope.save= function() {
    $scope.updateFocused();
    $scope.saving = true;
    imageService.save($scope.image, $scope.paths)
    .success(function(data) {
      $scope.alerts.push(data);
      $scope.saving = false;
    })
    .error(function(data) {
      $scope.alerts.push(data);
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

})

