angular.module('anatomy.tagging.controllers', [])

.controller('anatomyMain', function($scope) {
})

.controller('TermsController', 
    function($scope, termsService, $window, $location, imageService) {
  $scope.loading = true;
  $scope.Math = $window.Math;
  $scope.parts = [{
    key : 'H',
    label : 'Hlava',
  }, {
    key : 'N',
    label : 'Krk',
  }, {
    key : 'C',
    label : 'Hrudní koš',
  }, {
    key : 'A',
    label : 'Břicho',
  }, {
    key : 'P',
    label : 'Pánev',
  }, {
    key : 'UE',
    label : 'Horní končetina',
  }, {
    key : 'LE',
    label : 'Dolní končetina',
  }];

  var urlParts = $location.absUrl().split('/');
  var image = urlParts[urlParts.length - 1];

  termsService.get(image).success(function(data) {
    $scope.terms = data;
    $scope.loading = false;
  });

  $scope.save = function(term) {
    term.saving = true;
    termsService.save(term).success(function(data) {
      term.alerts = term.alerts || [];
      term.alerts.push(data);
      term.saving = false;
    }).error(function(data) {
      term.alerts = term.alerts || [];
      term.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba.',
      });
      term.saving = false;
    });
  };

  imageService.get().success(function(data){
    $scope.image = data.image;
  });

  $scope.closeAlert = function(term, index) {
    term.alerts.splice(index, 1);
  };

  termsService.get().success(function(data) {
    $scope.allTerms = data;
  });

})

.controller('ImageListController', function($scope, imageService, $window, $routeParams) {
  $scope.Math = $window.Math;
  $scope.loading = true;
  $scope.section = $routeParams.section;
  $scope.alerts = [];

  imageService.all(true).success(function(data) {
    processImages(data.images);
    $scope.loading = false;

    imageService.all().success(function(data) {
      processImages(data.images);
    });
  }).error(function() {
    $scope.alerts.push({
      type : 'danger',
      msg : 'Na serveru nastala chyba',
    });
    $scope.loading = false;
  });

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  function processImages(images) {
    $scope.imagesByCategory = {};
    for (var i = 0; i < images.length; i++) {
      var categoryName = images[i].category && images[i].category.name_cs;
      var slug = (categoryName || 'null').replace(/ /g, '-');
      if (!$scope.imagesByCategory[slug]) {
        $scope.imagesByCategory[slug] = {
          name : categoryName,
          slug : slug,
          progress : Math.floor((Math.random() * 100) + 1),
          images : [],
        };
      }
      $scope.imagesByCategory[slug].images.push(images[i]);
    }
    $scope.images = images;
  }
})

.controller('ImageController', function($scope, imageService, termsService, colorService, Slug) {
  $scope.pathsByColor = {};
  $scope.loading = true;
  $scope.alerts = [];
  $scope.pathsByTerm = {};
  $scope.byTermByTermId = {};
  $scope.pathsBys = [
    {
      heading  : 'Podle barev',
      obj : $scope.pathsByColor,
    }, {
      heading  : 'Podle pojmů',
      obj : $scope.pathsByTerm,
    }
  ];

  termsService.get().success(function(data) {
    $scope.terms = data;
  });

  imageService.get().success(function(data){
    $scope.image = data.image;
    $scope.paths = data.paths;
    for (var i = 0; i < data.paths.length; i++) {
      var p = data.paths[i];
      var c = p.color;
      if (p.term && p.term.code == 'too-small') {
        continue;
      }
      $scope.pathTermUpdated(p);
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
          color : p.color,
        };
      }
      $scope.pathsByColor[c].paths.push(p);
      if ($scope.pathsByColor[c].term && $scope.pathsByColor[c].term.code && 
          (!p.term || $scope.pathsByColor[c].term.code != p.term.code)) {
        $scope.pathsByColor[c].showDetails = true;
        $scope.pathsByColor[c].term = {
          code : 'split',
          name_la : 'Rozděleno na podčásti',
        };
        $scope.pathsByColor[c].disabled = false;
      }
      if (!$scope.pathsByColor[c].term || 
          $scope.pathsByColor[c].term.code !== 'split') {
        $scope.pathsByColor[c].term = p.term;
      }
      if ($scope.pathsByColor[c].term && 
          $scope.pathsByColor[c].term.code === 'no-practice') {
        $scope.pathsByColor[c].disabled = true;
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
    if (byColor.showDetails) {
      byColor.term = {
        code : 'split',
        name_la : 'Rozděleno na podčásti',
      };
    }
    $scope.updateFocused();
  };

  $scope.updateFocused = function() {
    if ($scope.focused) {
      if ($scope.focused.paths) {
        $scope.termUpdated($scope.focused);
      } else {
        $scope.pathTermUpdated($scope.focused);
      }
    }
  };

  $scope.focus = function(byColor) {
    $scope.updateFocused();
    $scope.focused = byColor;
    imageService.focus(byColor);
  };

  $scope.termUpdated = function(byColor) {
    if (byColor.term && byColor.term.code === 'split') {
      return;
    }
    if (byColor.paths) {
      for (var i = 0; i < byColor.paths.length; i++) {
        byColor.paths[i].term = byColor.term;
        $scope.pathTermUpdated(byColor.paths[i]);
        byColor.paths[i].disabled = byColor.term && byColor.term.code === 'no-practice';
      }
    }
  };

  $scope.pathTermUpdated = function(p) {
    var slug = p.term ? Slug.slugify(p.term.name_la) : 'zzz-empty';
    var oldByTerm = $scope.byTermByTermId[p.id];
    if (oldByTerm && oldByTerm != $scope.pathsByTerm[slug]) {
      oldByTerm.paths  = oldByTerm.paths.filter(function(path) {
        return p.id != path.id;
      });
    }
    if (!$scope.pathsByTerm[slug]) {
      $scope.pathsByTerm[slug] = {
        term : p.term,
        paths : [],
        color : p.color,
      };
    }
    if (oldByTerm != $scope.pathsByTerm[slug]) {
      $scope.pathsByTerm[slug].paths.push(p);
    }
    $scope.byTermByTermId[p.id] = $scope.pathsByTerm[slug];
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
      $scope.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba',
      });
      $scope.saving = false;
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

})

.controller('PracticeController', function($scope, imageService, termsService, colorService, practiceService, $routeParams, $timeout, $filter, colors) {
  $scope.loading = true;
  $scope.progress = 0;

  imageService.get($routeParams.image).success(function(data){
     $scope.image = data.image;
  });

  practiceService.getQuestions($routeParams.image).success(function(data) {
    $scope.loading = false;
    $timeout(function() {
      $scope.imageController.click(function(clickedCode) {
        var isInOptions = !$scope.question.options || 
            $scope.question.options.filter(function(o) {
              return o.code == clickedCode;
            }).length == 1;
        if ($filter('isFindOnMapType')($scope.question) && isInOptions) {
          $scope.checkAnswer(clickedCode);
        }
      });
      $scope.next();
    }, 500);
  });

  $scope.highlight = function() {
    if ($scope.imageController) {
      $scope.imageController.clearHighlights();
      if ($filter('isPickNameOfType')($scope.question)) {
        $scope.imageController.highlightTerm($scope.question.asked_code, colors.NEUTRAL);
      }
      if ($filter('isFindOnMapType')($scope.question) && $scope.question.options) {
        for (var i = 0; i < $scope.question.options.length; i++) {
          $scope.imageController.highlightTerm(
            $scope.question.options[i].code, colors.HIGHLIGHTS[i]);
        }
      }
    }
  };

  $scope.next = function() {
    if ($scope.progress < 100) {
      $scope.question = practiceService.next();
      $scope.questions = [$scope.question];
      $scope.question.asked_code = $scope.question.code;
      $scope.canNext = false;
      $scope.highlight();
    } else {
      setupSummary();
    }
  };

  $scope.checkAnswer = function(answered_code) {
    $scope.question.answered_code = answered_code;
    var asked = $scope.question.code;
    $scope.progress = practiceService.answer($scope.question);
    highlightAnswer(asked, answered_code);

    if (asked == answered_code) {
      $timeout(function() {
        $scope.next();
      }, 700);
    } else {
      $scope.canNext = true;
    }
  };

    function setupSummary() {
      $scope.questions.pop();
      $scope.question.slideOut = true;
      $scope.layer = undefined;
      // prevents additional points gain. issue #38
      $scope.summary = practiceService.summary();
      $scope.showSummary = true;
      $scope.imageController.clearHighlights();
      //$scope.imageController.showSummaryTooltips($scope.summary.questions);
      angular.forEach($scope.summary.questions, function(q) {
        var correct = q.asked_code == q.answered_code;
        $scope.imageController.highlightTerm(q.asked_code, correct ? colors.GOOD : colors.BAD, 1);
      });
      //$("html, body").animate({ scrollTop: "0px" });
      //events.emit('questionSetFinished', user.getUser().answered_count);
    }

    function highlightAnswer (asked, selected) {
      if (asked != selected) {
        $scope.imageController.highlightTerm(selected, colors.BAD);
      }
      $scope.imageController.highlightTerm(asked, colors.GOOD);
      if ($filter('isPickNameOfType')($scope.question)) {
        highlightOptions(selected);
      }
    }

    function highlightOptions(selected) {
      $scope.question.options.map(function(o) {
        o.correct = o.code == $scope.question.asked_code;
        o.selected = o.code == selected;
        o.disabled = true;
        return o;
      });
    }
});

