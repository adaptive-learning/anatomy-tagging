angular.module('anatomy.tagging', ['ui.bootstrap', 'ngCookies'])

.controller('anatomyMain', function($scope, imageService, termsService) {
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
      if (c[1] == c[3] && c[3] == c[5] && (!p.term || p.term.code === 'no-practice')) {
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
      //$scope.pathsByColor[c].containsActive ;
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
      $scope.loading = false;
    }
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
  };

  $scope.focus = function(byColor) {
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

.service('termsService', function($http) {
  return {
    get : function() {
      var url = '/terms';
      var promise = $http.get(url);
      return promise;
    }
  };
})

.service('imageService', function($http, $location ,$cookies) {
  var focusListeners = [];
  var promise;
  return {
    get : function() {
      var urlParts = $location.absUrl().split('/');
      var url = '/imagejson/' + urlParts[urlParts.length - 1];
      promise = promise || $http.get(url);
      return promise;
    },
    bindFocus : function(callback) {
      focusListeners.push(callback);
    },
    focus : function(path) {
      for (var i = 0; i < focusListeners.length; i++) {
        focusListeners[i](path);
      }
    },
    save : function(image, paths) {
      var url = "/image/update";
      var data = {
        image: image,
        paths: paths,
      };
      $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      return $http.post(url, data);
    }
  };
})

.directive('image', function(imageService, $window) {
  var paths = [];
  var pathsObj = {};
  var rPathsObj = {};
  var focusRect;
  var paperBBox = {
    x : 0,
    y : 0,
  };
  var focused = [];
  return {
      restrict: 'C',
      scope: {
          dset: '='
      },
      link: function(scope, element, attrs) {
          imageService.get(attrs.url).success(function(data){
            paperBBox.x = data.image.x;
            paperBBox.y = data.image.y;
            paperBBox.width = data.image.width;
            paperBBox.height = data.image.height;
            var paperWidth = $window.innerWidth * (7 /12);
            var paperHeight = $window.innerHeight - 100;
            var r = Raphael(element[0], paperWidth, paperHeight);
            r.setViewBox(paperBBox.x, paperBBox.y, paperBBox.width, paperBBox.height, false);

            for (var i = 0; i < data.paths.length; i++) {
              var p = data.paths[i];
              path = r.path(p.d);
              path.attr({
                'fill' : p.color,
                'opacity' : p.opacity,
                'stroke-width' : 0,
                'stroke' : 'red',
                'cursor' : 'pointer',

              });
              path.data('id', p.id);
              path.click(function(){
                //console.log(this.data('id'));
                var p = pathsObj[this.data('id')];
              });
              var bbox = path.getBBox();
              if (bbox.width < 5 || bbox.height < 5) {
                p.isTooSmall = true;
                p.term = {
                  code : 'too-small',
                };
              }
              paths.push(path);
              rPathsObj[p.id] = path;
              pathsObj[p.id] = p;
            }

            paperBBox = getBBox(paths.map(function(p) {return p.getBBox();}));
            data.image.x = paperBBox.x;
            data.image.y = paperBBox.y;
            data.image.width = paperBBox.width;
            data.image.height = paperBBox.height;
            r.setViewBox(paperBBox.x, paperBBox.y, paperBBox.width, paperBBox.height, true);

            var initMapZoom = function(paper, options) {
              var panZoom = paper.panzoom(options);
              panZoom.enable();
        
              $('#zoom-in').click(function(e) {
                panZoom.zoomIn(1);
                e.preventDefault();
              }); 
        
              $('#zoom-out').click(function(e) {
                panZoom.zoomOut(1);
                e.preventDefault();
              }); 
              return panZoom;
            };
            var panZoomOptions = {
             initialPosition : {
               x : paperBBox.x,
               y : paperBBox.y,
             }
            };
            //initMapZoom(r, panZoomOptions);

            focusRect = r.rect(-100,10, 10, 10);
            focusRect.attr({
                'stroke-width' : 5,
                'stroke' : 'red',
            });

            imageService.bindFocus(function(pathOrByColor) {
              clearFocused();
              if (pathOrByColor.d) {
                focusPath(pathOrByColor);
              } else {
                var bboxes = [];
                for (var i = pathOrByColor.paths.length - 1; i >= 0; i--) {
                  var bbox = focusPath(pathOrByColor.paths[i]);
                  if (bbox){
                    bboxes.push(bbox);
                  }
                }
                var bigBBox = getBBox(bboxes);
                animateFocusRect(bigBBox);
              }
            });

            function clearFocused() {
              for (var i = 0; i < focused.length; i++) {
                focused[i].attr('stroke-width', 0);
              }
              focused = [];
            }

            function focusPath(path) {
              if (path.isTooSmall) {
                return;
              }
              var rPath = rPathsObj[path.id];
              var bbox = (rPath.getBBox());
              animateFocusRect(bbox);
              focused.push(rPath);
              rPath.attr('stroke-width', 3);
              rPath.toFront();
              //console.log(bbox);
              return bbox;
            }

            function animateFocusRect(bbox) {
              focusRect.attr(paperBBox);
              focusRect.animate(enlargeABit(bbox), 200, '>');
              focusRect.toFront();
            }

            function enlargeABit(bbox) {
              var bit = 2;
              bbox.x -= bit;
              bbox.y -= bit;
              bbox.width += 2 * bit;
              bbox.height += 2 * bit;
              return bbox;
            }

            function getBBox(bboxes) {
              var xs = bboxes.map(function(b){return b.x;});
              var minX = Math.min.apply(Math, xs);
              var ys = bboxes.map(function(b){return b.y;});
              var minY = Math.min.apply(Math, ys);
              var x2s = bboxes.map(function(b){return b.x2;});
              var maxX = Math.max.apply(Math, x2s);
              var y2s = bboxes.map(function(b){return b.y2;});
              var maxY = Math.max.apply(Math, y2s);
              return {
                x : minX,
                y : minY,
                width : maxX - minX,
                height : maxY - minY,
              };
            }
          });
      }
  };
});
