angular.module('anatomy.tagging', [
  'anatomy.tagging.controllers',
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

}])

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
            var paperHeight = $window.innerHeight - 66;
            var r = Raphael(element[0], paperWidth, paperHeight);
            r.setViewBox(paperBBox.x, paperBBox.y, paperBBox.width, paperBBox.height, false);

            for (var i = 0; i < data.paths.length; i++) {
              var p = data.paths[i];
              path = r.path(p.d);
              path.attr({
                'fill' : p.color,
                'opacity' : p.opacity,
                'stroke-width' : p.stroke_width,
                'stroke' : p.stroke,
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
                var p = pathsObj[focused[i].data('id')];
                focused[i].attr('stroke-width', p.stroke_width);
                focused[i].attr('stroke', p.stroke);
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
              rPath.attr('stroke', 'red');
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
