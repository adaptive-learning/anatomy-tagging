angular.module('anatomy.tagging.services', [])

.service('termsService', function($http, $cookies) {
  return {
    get : function(image, showImages) {
      var url = '/termsjson/' + (image || '') + 
        (showImages ? '?images=True' : '');
      var promise = $http.get(url);
      return promise;
    },
    save : function(term) {
      var url = '/termsjson/update';
      $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      var promise = $http.post(url, term);
      return promise;
    },
    mergeTerms : function(term1, term2) {
      var url = '/termsjson/merge';
      $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      var data = {
        term1 : term1,
        term2 : term2,
      };
      var promise = $http.post(url, data);
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
      if (that.isGray(c)) {
        return c;
      }
      var rgb = that.hexToRgb(c);
      var weights =  [0.299, 0.587, 0.114];
      var graySum = 0;
      for (var i = 0; i < rgb.length; i++) {
        graySum += 3.7 * rgb[i] * weights[i];
      }
      var grayAverageHex = Math.round(graySum / 3).toString(16);
      if (grayAverageHex == 'NaN') {
        return '#000000';
      }
      return '#' + grayAverageHex + grayAverageHex + grayAverageHex;
    },
  };
  return that;
})

.service('imageService', function($http, $location ,$cookies) {
  var focusListeners = [];
  var promises = {};
  return {
    all : function(cached) {
      var url = '/imagejson/';
      if (cached && promises[url]){
        return promises[url];
      }
      var params = {};
      if (cached) {
        params.params = {
          omit_counts: true,
        };
      }
      var promise = $http.get(url, params);
      promises[url] = promise;
      return promise;
    },
    get : function(imageSlug) {
      var urlParts = $location.absUrl().split('/');
      var url = '/imagejson/' + (imageSlug || urlParts[urlParts.length - 1]);
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
    save : function(image, paths, _export) {
      var url = "/image/update";
      var data = {
        image: image,
        paths: paths,
        export: _export,
      };
      $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
      return $http.post(url, data);
    }
  };
})

.service('exportService', function($http, $routeParams) {
  var exportDomain = $routeParams.exportdomain || 'anatom.cz';
  return {
    export: function(image_slug) {
      var url = 'http://' + exportDomain + '/load_flashcards/?context=' +
        image_slug + '&callback=JSON_CALLBACK';
      var promise = $http.jsonp(url);
      return promise;
    }
  };
})

.service('practiceService', function(termsService, $location) {
  var callback;
  var questions = [];
  var index = 0;
  var summary = [];
  var items = [];

  function getType(type) {
    if (!type) {
      var i = Math.floor(Math.random() * 6) + 1;
      type = [10, 12, 14, 16, 22, 24, 26][i];
    }
    return type;
  }
  function getOptions(type) {
    var noOfOptions = type % 10;
    if (noOfOptions === 0) {
      return;
    } else {
      var options = items.concat(items).splice(index - 1, noOfOptions).map(function(o) {
        return angular.copy(o);
      });
      return shuffle(options);
    }

  }

  function getText(type) {
    if (type == 10) {
        return "Na obrázku vyber";
    } else if (type < 20) {
        return "Ze zvýrazněných částí obrázku vyber";
    } else {
        return "Jak se jmenuje zvýrazněná část obrázku";
    }
  }
  //+ Jonas Raoni Soares Silva
  //@ http://jsfromhell.com/array/shuffle [v1.0]
  function shuffle(o){ //v1.0
      for(var j, x, i = o.length; i; j = Math.floor(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
      return o;
  }

  return {
    getQuestions : function(imageSlug) {
      termsService.get(imageSlug).success(function(data){
          items = data;
          questions = angular.copy(data);
          if ($location.search().limit) {
            questions = questions.slice(0, $location.search().limit);
          }
          index = 0;
          callback(questions);
          summary = [];
      });
      return {
        success: function(fn) {
          callback = fn;
        }
      };
    },
    summary : function() {
      /*
      $analytics.eventTrack('finished', {
        category: 'practice',
        label: url,
      });
      */
      var correctlyAnswered = summary.filter(function(q) {
          return q.asked_code == q.answered_code;
        });
      return {
        correctlyAnsweredRatio : correctlyAnswered.length / summary.length,
        questions : summary
      };
    },
    answer : function() {
      var progress = summary.length / questions.length * 100;
      return progress;
    },
    next : function() {
      var q = angular.copy(questions[index++]);
      // Hack for controll
      q.type = 10; //getType($location.search().type);
      q.options = getOptions(q.type);
      q.text = getText(q.type);
      q.item = q.name_la;
      q.asked_code = q.id;
      summary.push(q);
      return q;
    },
    getItems : function() {
      return items;
    }
  };
});

