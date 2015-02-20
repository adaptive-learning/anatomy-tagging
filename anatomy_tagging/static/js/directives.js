angular.module('anatomy.tagging.directives', [])

.directive('image', function(imageService, $window, Slug) {
  var paths = [];
  var pathsObj = {};
  var rPathsObj = {};
  var focusRect;
  var viewBox = {
    x : 0,
    y : 0,
  };
  var focused = [];
  var glows = [];
  return {
      restrict: 'C',
      scope: {
          dset: '='
      },
      link: function(scope, element, attrs) {
          imageService.get(attrs.url).success(function(data){
            viewBox = data.image.bbox;
            var paper = {
              x : 0,
              y : 0,
            };
            var r = Raphael(element[0]);

            function clickHandler(){
              var input = $(".tab-pane.active .sub-parts:visible #input-" + this.data('id'));
              if (input.length === 0) {
                input = $(".tab-pane.active #input-" + this.attr('fill').substr(1));
              }
              var pathObj = pathsObj[this.data('id')];
              var termSlug = Slug.slugify(pathObj.term && pathObj.term.name_la);
              if (input.length === 0) {
                input = $(".tab-pane.active #input-" + termSlug);
              }
              input.focus();
            }

            for (var i = 0; i < data.paths.length; i++) {
              var p = data.paths[i];
              path = r.path(p.d);
              path.attr({
                'fill' : p.color,
                'opacity' : p.opacity,
                'stroke-width' : p.stroke_width,
                'stroke' : p.stroke,
                'cursor' : p.disabled ? 'default' : 'pointer',
              });
              path.data('id', p.id);
              path.click(clickHandler);
              p.bbox = p.bbox || path.getBBox();
              if (p.bbox.width < 5 || p.bbox.height < 5) {
                p.isTooSmall = true;
                p.term = {
                  code : 'too-small',
                };
              }
              paths.push(path);
              rPathsObj[p.id] = path;
              pathsObj[p.id] = p;
            }

            viewBox = getBBox(data.paths.map(function(p) {return p.bbox;}));
            data.image.bbox = viewBox;

            function onWidowResize(){
              paper.width = $window.innerWidth * (7 /12);
              paper.height = $window.innerHeight - 66;
              r.setSize(paper.width, paper.height);
              r.setViewBox(viewBox.x, viewBox.y, viewBox.width, viewBox.height, true);
            }
            onWidowResize();
            angular.element($window).bind('resize', function() {
              onWidowResize();
            });



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
               x : viewBox.x,
               y : viewBox.y,
             }
            };
            //initMapZoom(r, panZoomOptions);

            focusRect = r.rect(-100,10, 10, 10);
            focusRect.attr({
                'stroke-width' : 3,
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
              for (var i = 0; i < glows.length; i++) {
                glows[i].remove();
              }
              glows = [];
              for (i = 0; i < focused.length; i++) {
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
              animateFocusRect(path.bbox);
              focused.push(rPath);
              var focusAttr = {
                'stroke-width' : '3',
                'stroke' : 'red',
              };
              //rPath.animate(focusAttr, 500, '>');
              var glow = rPath.glow({
                'color': 'red',
                'opacity': 1,
                'width': 5,
              });
              glow.toFront();
              glows.push(glow);
              //rPath.toFront();
              //console.log(bbox);
              return path.bbox;
            }

            function animateFocusRect(bbox) {
              focusRect.attr(paper);
              focusRect.animate(enlargeABit(bbox), 500, '>');
              //focusRect.toFront();
            }

            function enlargeABit(oldBBox) {
              var bbox = angular.copy(oldBBox);
              var bit = 4;
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
