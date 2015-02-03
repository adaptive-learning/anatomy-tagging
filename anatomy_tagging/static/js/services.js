angular.module('anatomy.tagging.services', [])

.service('termsService', function($http) {
  return {
    get : function() {
      var url = '/terms';
      var promise = $http.get(url);
      return promise;
    }
  };
})

.service('colorService', function() {
  var that = {
    hexToRgb : function(c) {
      var red = parseInt(c.substr(1, 2), 16);
      var green = parseInt(c.substr(3, 2), 16);
      var blue = parseInt(c.substr(5, 2), 16);
      return [red, green, blue];
    },
    getDominantColor : function(c) {
      var rgb = that.hexToRgb(c);
      return rgb.indexOf(Math.max.apply(Math, arr));
    },
    isGray : function(c) {
      var rgb = that.hexToRgb(c);
      return Math.max(Math.abs(rgb[0] - rgb[1]), Math.abs(rgb[0] - rgb[2])) < 10;
    },
    toGrayScale : function(c) {
      var rgb = that.hexToRgb(c);
      var weights =  [0.299, 0.587, 0.114];
      var graySum = 0;
      for (var i = 0; i < rgb.length; i++) {
        graySum += 2.7 * rgb[i] * weights[i];
      }
      var grayAverageHex = Math.round(graySum / 3).toString(16);
      return '#' + grayAverageHex + grayAverageHex + grayAverageHex;
    },
  };
  return that;
})

.service('imageService', function($http, $location ,$cookies) {
  var focusListeners = [];
  var promises = {};
  return {
    all : function() {
      var url = '/imagejson/';
      var promise = $http.get(url);
      return promise;
    },
    get : function() {
      var urlParts = $location.absUrl().split('/');
      var url = '/imagejson/' + urlParts[urlParts.length - 1];
      var promise = promises[url] || $http.get(url);
      promises[url] = promise;
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

