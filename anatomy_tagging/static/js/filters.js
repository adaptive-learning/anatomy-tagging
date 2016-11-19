(function() {
  'use strict';
  /* Filters */
  angular.module('anatomy.tagging.filters', [])
  
  .value('gettext', function(x) {return x;})

  .filter('isFindOnMapType', function() {
    return function(question) {
      return question && question.type < 20;
    };
  })

  .filter('isPickNameOfType', function() {
    return function(question) {
      return question && question.type >= 20;
    };
  })

  .filter('percent', function() {
    return function(n) {
      n = n || 0;
      return Math.round(100 * n) + '%';
    };
  })

  .filter('codeToName', function(practiceService) {
    return function(code) {
      var items = practiceService.getItems();
      items = items.filter(function(i) {
        return i.code == code;
      });
      if (items.length == 1) {
        return items[0].name_la;
      } else {
        return code;
      }
    };
  })

  .filter('trans',['gettext', function(gettext) {
    return function(msgid) {
      return gettext(msgid);
    };
  }])

  .filter('empty', function() {
    return function(data, emptyField) {
      return !emptyField ? data : data && data.filter(function(row) {
        return !row[emptyField];
      });
    };
  });

})();
