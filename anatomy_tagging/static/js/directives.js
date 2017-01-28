angular.module('anatomy.tagging.directives', [])

.value('$', jQuery)

  .value('colors', {
    'GOOD': '#5CA03C',
    'BAD': '#e23',
    'NEUTRAL' : '#1d71b9',
    'BRIGHT_GRAY' : '#ddd',
    'WATER_COLOR' : '#73c5ef',
    'HIGHLIGHTS' : [
      '#f9b234',
      '#1d71b9',
      '#36a9e0',
      '#312883',
      '#fdea11',
      '#951b80',
    ],
  })
  

.directive('image', function(imageService, $window, Slug, simplify, $, colorService, $timeout) {
  var paths = [];
  var pathsObj = {};
  var pathsByCode = {};
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
            var clickFn;
            
            
            function taggingClickHandler(){
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

            function practiceClickHandler(){
              var clickedCode = this.data('code');
              if (clickedCode == 'no-practice' || scope.$parent.canNext) {
                return;
              }
              if (clickFn) clickFn(clickedCode);
              scope.$parent.$apply();
            }

            var highlights = [];
            var highlightsByCode = {};
            var highlightQueue = [];
            var highlightInProgress = false;
            var ANIMATION_TIME_MS = 500;

            var that = { 
              click: function(callback) {
                clickFn = callback;
              },
              _next : function() {
                if (highlightQueue.length > 0) {
                  item = highlightQueue.shift();
                  that._highlightTerm(item[0], item[1]);
                  $timeout(that._next, ANIMATION_TIME_MS / 2);
                } else {
                  highlightInProgress = false;
                }
              },
              highlightTerm : function(code, color) {
                highlightQueue.push([code, color]);
                if (!highlightInProgress) {
                  highlightInProgress = true;
                  that._next();
                }
              },
              _highlightTerm : function(code, color) {
                var paths = pathsByCode[code] || [];
                var bbox = getBBox(paths.map(function(p) {return p.getBBox();}));
                var centerX = Math.floor(bbox.x + bbox.width / 2);
                var centerY = Math.floor(bbox.y + bbox.height / 2);
                var clones = [];
                for (var i = 0; i < paths.length; i++) {
                  var clone = paths[i].clone();
                  clone.click(clickHandler);
                  clone.hover(hoverInHandler, hoverOutHandler);
                  clone.data('id', paths[i].data('id'));
                  clone.data('code', code);
                  clone.data('opacity', paths[i].data('opacity'));
                  clone.data('color', color);
                  clone.attr({
                    'fill' : color,
                  });
                  clones.push(clone);
                  var animAttrs = {
                    transform : 's' + [1.5, 1.5, centerX, centerY].join(','),
                  };
                  (function(clone){
                    clone.animate(animAttrs, ANIMATION_TIME_MS / 2, '>', function() {
                      clone.animate({
                        transform : '',
                      }, ANIMATION_TIME_MS / 2, '<');
                    });
                  })(clone);
                }
                highlightsByCode[code] = clones;
                highlights = highlights.concat(clones);
              },

              clearHighlights : function() {
                for (var i = 0; i < highlights.length; i++) {
                  highlights[i].remove();
                }
                highlights = [];
                highlightsByCode = {};
              },
              refreshBbox : function() {
                viewBox.updated = true;
                r.setViewBox(viewBox.x, viewBox.y, viewBox.width, viewBox.height, true);
              },
            };

            scope.$root.imageController = that;

            var clickHandler;
            var hoverOpacity = 0;
            if (attrs.tagging) {
              clickHandler = taggingClickHandler;
            } else {
              clickHandler = practiceClickHandler;
              hoverOpacity = 0.2;
            }
              hoverInHandler = function() {
                setLowerOpacity(this, hoverOpacity);
              };
              hoverOutHandler = function() {
                setLowerOpacity(this, 0);
              };

            function setLowerOpacity(path, decrease) {
                var code = path.data('code');
                if (code == 'no-practice') {
                  return;
                }
                var paths = (pathsByCode[code] || []).concat(
                    highlightsByCode[code] || []);
                for (var i = 0; i < paths.length; i++) {
                  paths[i].attr({
                    'opacity' : paths[i].data('opacity') - decrease,
                  });
                }
            }

            for (var i = 0; i < data.paths.length; i++) {
              var p = data.paths[i];
              simplePathString = p.d; //simplify(p.d);
              path = r.path(simplePathString);
              var color = attrs.tagging ? p.color : colorService.toGrayScale(p.color);
              path.attr({
                'fill' : color,
                'opacity' : p.opacity,
                'stroke-width' : p.stroke_width,
                'stroke' : p.stroke,
                'cursor' : p.disabled ? 'default' : 'pointer',
              });
              path.data('id', p.id);
              path.data('color', color);
              path.data('opacity', p.opacity);
              path.click(clickHandler);
              path.hover(hoverInHandler, hoverOutHandler);
              p.bbox = p.bbox || path.getBBox();
              if (p.bbox.width < 4 && p.bbox.height < 4 && p.bbox.width / data.image.bbox.width < 0.01 && p.bbox.height / data.image.bbox.height < 0.01) {
                p.isTooSmall = true;
                p.term = {
                  code : 'too-small',
                };
              } else if (p.term && p.term.code == 'too-small') {
                p.term = undefined;
              }
              paths.push(path);
              rPathsObj[p.id] = path;
              var code = p.term && p.term.code;
              path.data('code', code);
              if (!pathsByCode[code]) {
                pathsByCode[code] = [];
              }
              pathsByCode[code].push(path);
              pathsObj[p.id] = p;
            }

            viewBox = getBBox(data.paths.map(function(p) {return p.bbox;}));
            data.image.bbox = viewBox;

            function onWidowResize(){
              paper.width = $window.innerWidth * (7 /12);
              paper.height = ($window.innerHeight - 66) * (attrs.relativeHeight || 1);
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

            var zoomStep = 0.1;
            var initialZoomX = (1 - viewBox.width/paper.width) / zoomStep;
            var initialZoomY = (1 - viewBox.height/paper.height) / zoomStep;
            var initialZoom = Math.min(initialZoomX, initialZoomY);
            var panZoomOptions = {
             initialPosition : {
               x : viewBox.x - Math.max(0,
                 (paper.width / (paper.height / viewBox.height) - viewBox.width) / 2),
               y : viewBox.y - Math.max(0, 
                 (paper.height / (paper.width / viewBox.width) - viewBox.height) / 2),
             },
             initialZoom : initialZoom,
             minZoom : initialZoom,
             zoomStep : zoomStep,
            };
            initMapZoom(r, panZoomOptions);
            scope.zoomInited = true;

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
})

.factory('simplify', function() {

  function convertPoint(pointArray) {
    var command = pointArray[0].toLowerCase();
    var x, y;
    var indexes = {
      'c' : [5, 6],
      's' : [3, 4],
      'l' : [1, 2],
      'm' : [1, 2],
      'h' : [1, -1],
      'v' : [-1, 1],
      'z' : [-1, -1],
    };
    xy = indexes[command];
    if (!xy) {
      alert ("error " + pointObj);
      throw pointArray;
    }
    var pointObj = {
      c : pointArray[0],
      x : parseFloat(pointArray[xy[0]]) || 0,
      y : parseFloat(pointArray[xy[1]]) || 0,
    };
    return pointObj;
  }

  function parsePathData(pathData) {
      var tokenizer = /([a-z]+)|([+-]?(?:\d+\.?\d*|\.\d+))/gi,
          match,
          current,
          commands = [];

      tokenizer.lastIndex = 0;
      while (match = tokenizer.exec(pathData))
      {
          if (match[1])
          {
              if (current) commands.push(current);
              current = [ match[1] ];
          }
          else
          {
              if (!current) current = [];
              current.push(match[2]);
          }
      }
      if (current) commands.push(current);
      return commands;
  }

  function simplifyPath (path, minLength) {
    var newPath = [];
    var lastPos = [path[0][1], path[0][2]];
    var pos;
    for (var i = 0; i < path.length; i++) {
      var pa = path[i];
      var p = convertPoint(pa);
      if (p.c.toLowerCase() == p.c) {
        p.c = p.c.toUpperCase();
        p.x = pos[0] + p.x;
        p.y = pos[1] + p.y;
        if ('SCL'.indexOf(p.c) != -1) {
          pa[0] = p.c;
          for (var j = 1; j < pa.length; j++) {
            pa[j] = pos[(j + 1) % 2] + parseFloat(pa[j]);
          }
        }
      }
      pos = [p.x, p.y];
      if ('SCL'.indexOf(p.c) == -1 || Math.max(Math.abs(pos[0] - lastPos[0]), 
          Math.abs(pos[1] - lastPos[1])) > minLength) {
        lastPos = pos;
        newPath.push(pa);
      } else {
        //console.log(pos[0], lastPos[0], pos[1], lastPos[1]);
      }
    }
    return newPath;
  }

  return function(path) {
    var parsedPath = parsePathData(path);
    var simplifiedPath = simplifyPath(parsedPath, 0.2);
    var simplePathString = simplifiedPath.map(function(p) {
      return p.join(' ');
    }).join(' ');
    if (parsedPath.length > 100) {
      console.log(parsedPath.length, simplifiedPath.length);
    }
    return simplePathString;
  };
})

.directive('termEdit', function() {
  return {
    restrict: 'A', 
      scope: {
        term: '=term',
      },   
    templateUrl : 'static/tpl/term_edit.html',
  };
})

.directive('tablePager', function() {
  return {
    restrict: 'A', 
      scope: {
        data: '=tablePager',
        page: '=page',
        pageSize: '=pageSize',
      },   
    templateUrl : 'static/tpl/pager.html',
    link: function(scope) {
      scope.Math = Math;
    }
  };
})

.directive('scrollTopOnClick', function() {
  return {
    restrict: 'A',
    link: function(scope, $elm) {
      $elm.on('click', function() {
        $("body").animate({scrollTop: 0}, 200);
      });
    }
  };
});
