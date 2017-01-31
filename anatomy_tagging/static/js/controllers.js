angular.module('anatomy.tagging.controllers', [])

.controller('anatomyMain', function($scope) {
})

.controller('TermsController',
    function($scope, termsService, $window, $location, imageService,
      $routeParams, mergeTermsModal) {
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
  $scope.search = $routeParams.search;
  $scope.emptyField = $routeParams.empty;
  $scope.page = 1;
  $scope.pageSize = 20;
  $scope.showCode = $routeParams.showcode || $routeParams.usedonly;
  $scope.usedOnly = $routeParams.usedonly;
  var image = urlParts[urlParts.length - 1].split('?')[0];

  termsService.get(image, $scope.showCode, $scope.usedOnly).success(function(data) {
    $scope.terms = data;
    if ($scope.emptyField) {
      $scope.terms = $scope.terms.filter(function(row) {
        return !row[$scope.emptyField];
      });
    }
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

  if (image && image != 'duplicate') {
    imageService.get().success(function(data){
      $scope.image = data.image;
    });
  }

  $scope.closeAlert = function(term, index) {
    term.alerts.splice(index, 1);
  };

  termsService.get(undefined, $scope.showCode).success(function(data) {
    $scope.allTerms = data;
  });

  $scope.selectTerm = function(term) {
    if ($scope.selectedTerm) {
      mergeTermsModal.open($scope.selectedTerm, term);
      $scope.selectedTerm = undefined;
    } else {
      $scope.selectedTerm = term;
    }
  };

})

.factory('mergeTermsModal', ['$modal', function($modal) {
    return {
        open: function(term1, term2) {
            $modal.open({
                templateUrl: 'static/tpl/merge-terms.html',
                controller: 'MergeTerms',
                size: 'lg',
                resolve: {
                  term1 : function() {
                    return term1;
                  },
                  term2 : function() {
                    return term2;
                  },
                },
            });
        }
    };
}])

.controller('MergeTerms', function($scope, $modalInstance, termsService,
    exportService, term1, term2, $routeParams) {
  $scope.term1 = term1;
  $scope.term2 = term2;
  $scope.alerts = [];
  $scope.exportDomain = $routeParams.exportdomain || 'anatom.cz';

  $scope.mergeTerms = function(){
    $scope.saving = true;
    termsService.mergeTerms(term1, term2).success(function() {
      angular.forEach(term1.images, deployImage);
    }).error(function(data) {
      $scope.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba při slučování pojmů',
      });
    });
  };

  function deployImage(image) {
      exportService.export(image).success(function(data) {
        $scope.alerts.push(data);
        $scope.saving = false;
      }).error(function(data) {
        $scope.alerts.push({
          type : 'danger',
          msg : 'Na serveru nastala chyba při nahrávání obrázků. Pojmy jsou ale sloučeny. Otevři si obrázky a zkus nahrát každý zvlášť.',
        });
        $scope.saving = false;
      });
  }

  $scope.cancel = function(){
    $modalInstance.dismiss('cancel');
  };
})

.controller('ImageListController', function($scope, imageService, $window, $routeParams, termsService, colors) {
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
  // section stuff

  $scope.activateImage = function(image) {
    $scope.activeImage = $scope.activeImage != image ? image : null;
    if ($scope.activeImage) {
      termsService.get(image.filename_slug).success(function(data){
          $scope.terms = data;
      });
    }
  };
  var i = 0;
  $scope.clickTerm = function(term) {
    $scope.activeTerm = term;
    $scope.$root.imageController.clearHighlights();
    $scope.$root.imageController.highlightTerm(term.code,
      colors.HIGHLIGHTS[i++ % colors.HIGHLIGHTS.length]);

  };
})

.controller('ImageController', function($scope, imageService, termsService, colorService, Slug, $routeParams, exportService) {
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
  $scope.showBbox = $routeParams.showbbox;
  $scope.exportDomain = $routeParams.exportdomain || 'anatom.cz';
  if ($routeParams.exportdomain) {
    $scope.forceexport = true;
  }

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

  $scope.save = function(production) {
    $scope.updateFocused();
    $scope.saving = true;
    imageService.save($scope.image, $scope.paths, production)
    .success(function(data) {
      if (!production || data.type != 'success') {
        $scope.alerts.push(data);
        $scope.saving = false;
      } else if (production) {
        exportService.export($scope.image.filename_slug).success(function(data) {
          $scope.alerts.push(data);
          $scope.saving = false;
        }).error(function(data) {
          $scope.alerts.push({
            type : 'danger',
            msg : 'Na serveru nastala chyba',
          });
          $scope.saving = false;
        });
      }
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
      $scope.$root.imageController.click(function(clickedCode) {
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
    if ($scope.$root.imageController) {
      $scope.$root.imageController.clearHighlights();
      if ($filter('isPickNameOfType')($scope.question)) {
        $scope.$root.imageController.highlightTerm($scope.question.asked_code, colors.NEUTRAL);
      }
      if ($filter('isFindOnMapType')($scope.question) && $scope.question.options) {
        for (var i = 0; i < $scope.question.options.length; i++) {
          $scope.$root.imageController.highlightTerm(
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
      $scope.$root.imageController.clearHighlights();
      //$scope.$root.imageController.showSummaryTooltips($scope.summary.questions);
      angular.forEach($scope.summary.questions, function(q) {
        var correct = q.asked_code == q.answered_code;
        $scope.$root.imageController.highlightTerm(q.asked_code, correct ? colors.GOOD : colors.BAD, 1);
      });
      //$("html, body").animate({ scrollTop: "0px" });
      //events.emit('questionSetFinished', user.getUser().answered_count);
    }

    function highlightAnswer (asked, selected) {
      if (asked != selected) {
        $scope.$root.imageController.highlightTerm(selected, colors.BAD);
      }
      $scope.$root.imageController.highlightTerm(asked, colors.GOOD);
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
})

.controller('RelationsTreeController', function($scope, $http, $routeParams, $cookies, exportService) {
  $scope.type = $routeParams.type;
  $scope.filter = $routeParams.filter;
  $scope.alerts = [];
  $scope.exportDomain = $routeParams.exportdomain || 'anatom.cz';
  $http.get('/relationtree?relations=["' + $routeParams.type + '"]' + ($scope.filter == 'all' ? '&all=1' : '')).success(function(data) {
    $scope.relations = data.relations;

    var relation = data.relations[data.next];
    if (relation.children.length) {
      for (var j = 0; j < relation.children.length; j++) {
        relation.children[j] = $scope.relations[relation.children[j]];
      }
    }
    relation.index = 1;
    $scope.relationsList = [relation];
    for (var i=2; relation.next; i++) {
      relation = data.relations[relation.next];
      relation.index = i;
      if (!relation.parent_ids || !relation.parent_ids.length) {
        $scope.relationsList.push(relation);
      }
      if (relation.children.length) {
        for (var j = 0; j < relation.children.length; j++) {
          relation.children[j] = $scope.relations[relation.children[j]];
        }
      }
    }
    $scope.relationsCount = Object.keys($scope.relations).length;

    if (data.next_to_process) {
      $scope.setActiveById(data.next_to_process);
    } else {
      $scope.setActiveById(data.next);
    }
  });

  $scope.next = function() {
    $scope.setActiveById($scope.relation.next);
  };

  $scope.nextToProcess = function() {
    $scope.setActiveById($scope.relation.next_to_process);
  };

  $scope.previous = function() {
    $scope.setActiveById($scope.relation.previous);
  };

  $scope.addChild = function(relation) {
    $scope.setActive({
      term1: relation.term2,
      term2: {},
      type: relation.type,
      parent_ids: [relation.id],
    });
  };

  $scope.setActive = function(relation) {
    if ($scope.relation) {
      $scope.relation.active = false;
    }
    $scope.relation = relation;
    $scope.relation.active = true;
    $scope.relation.terminal = $scope.relation.labels &&
      $scope.relation.labels.indexOf('terminal') != -1;
    $scope.relation.siblings = $scope.getSiblings(relation);
    $scope.relation.breadCrumbs = $scope.getBreadCrumb(relation);
  };

  $scope.setActiveById = function(id) {
    $scope.setActive($scope.relations[id]);
  };

  $scope.getSiblings = function(relation) {
    if (!relation.parent_ids) {
      return [];
    }
    var result = [];
    relation.parent_ids.forEach(function(parent_id) {
      var par = $scope.relations[parent_id];
      var siblings = par.children.filter(function(child) {
        return child.id != relation.id;
      });
      if (siblings.length > 0) {
        siblings.forEach(function(sib) {
          result.push([par, sib]);
        });
      }
    });
    return result;
  };

  $scope.getBreadCrumb = function(relation) {
    var parentPath = $scope.getParentPath(relation);
    var crumps = parentPath.map(function(relations) {
      var relation = relations[0];
      return {
        name: relation.term2.name_la ? relation.term2.name_la : relation.term2.name_en,
        relation_id: relation.id
      }
    });
    crumps.unshift({
      name: parentPath[0][0].term1.name_la ? parentPath[0][0].term1.name_la : parentPath[0][0].term1.name_en,
      relation_id: parentPath[0][0].id
    });
    return crumps;
  };

  $scope.getParentPath = function(relation) {
    var path = [[relation]];
    var i = 0;
    var parents = function(parent_id) {
      return $scope.relations[parent_id];
    };
    while (relation) {
      if (relation.parent_ids) {
        path.push(relation.parent_ids.map(parents));
        relation = $scope.relations[relation.parent_ids[0]];
      } else {
        relation = undefined;
      }
      i = i + 1;
      if (i > 10) {
        return;
      }
    }
    path.reverse();
    return path;
  };

  $scope.updateTree = function(clientRelation, savedRelation) {
    $scope.relations[savedRelation.id] = savedRelation;
    clientRelation.parent_ids.forEach(function(parent_id) {
      var parent = $scope.relations[parent_id];
      if (!clientRelation.id) {
        // we have a new item, let's add it to the tree
        var previous;
        if (!parent.children || !parent.children.length) {
          parent.children = [];
          previous = parent;
        } else {
          previous = parent.children[parent.children.length -1];
        }
        savedRelation.next = previous.next;
        savedRelation.next_to_process = previous.next_to_process;
        savedRelation.previous = previous.id;
        previous.next = savedRelation.id;
        $scope.relations[savedRelation.next].previous = savedRelation.id;
        parent.children.push(savedRelation);
      }
    });
  };

  $scope.save = function(relation, state) {
    relation.saving = true;
    var data = [];
    data.push({
      name : relation.type.identifier,
      text1 : relation.text1,
      text2 : relation.text2,
      term1 : relation.term1,
      term2 : relation.term2,
      id : relation.id,
      state : state,
      labels : relation.terminal ? ['terminal'] : [],
    });
    relation.alerts = [];
    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
    $http.post("relationtree/update", data).success(function(data) {
      $scope.updateTree(relation, data[0]);
      $scope.relation = data[0];
      relation.alerts.push({
        type : 'success',
        msg : 'Souvislost byla úspěšně uložena.',
      });
      relation.saving = false;
    }).error(function(data) {
      relation.alerts = relation.alerts || [];
      relation.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba.',
      });
      relation.saving = false;
    });
  };

  $scope.publish = function(type) {
    $scope.saving = type;
    type = type.replace(' ', '-');
    $http.get("relationsexport/" + type + '?empty=true').success(function(data) {
      exportService.export(type).success(function(data) {
        $scope.alerts.push(data);
        $scope.saving = false;
      }).error(function(data) {
        $scope.alerts.push({
          type : 'danger',
          msg : 'Na serveru nastala chyba',
        });
        $scope.saving = false;
      });
    })
    .error(function(data) {
      $scope.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba',
      });
      $scope.saving = false;
    });
  };
})

.controller('RelationsController',
    function($scope, $http, termsService, $cookies, $routeParams, exportService) {
  $scope.loading = true;
  $scope.search = $routeParams.search;
  $scope.search2 = $routeParams.search;
  var source = $routeParams.source || 'List_of_muscles_of_the_human_body';
  $scope.mainTerm = {
    'List_of_muscles_of_the_human_body' : 'Muscle',
    'List_of_foramina_of_the_human_body' : 'Foramina',
    'FMA_branching_taid' : 'Artery',
  }[source];
  $scope.page = 1;
  $scope.pageSize = 20;
  var mainTerm = $scope.mainTerm;
  var url = "relationsjson/" + source;
  $http.get(url).success(function(data) {
    $scope.relationsDict = {};
    $scope.relationTypes = [];
    $scope.relations = [];
    for (var i = 0; i < data.raw.length; i++) {
      var r = data.raw[i];
      var key = r.text1.trim();
      var rObject = $scope.relationsDict[key];
      if (!rObject) {
        rObject = {};
        $scope.relations.push(rObject);
        $scope.relationsDict[key] = rObject;
      }
      rObject[mainTerm] = {
        term : r.term1,
        text : r.text1,
      };
      rObject[r.type] = rObject[r.type] || {
        terms : [],
        texts : [],
      };
      if (r.term2) {
          rObject[r.type].terms.push({term: r.term2});
      }
      if (r.text2) {
        rObject[r.type].texts.push(r.text2);
      }
      if ($scope.relationTypes.indexOf(r.type) == -1) {
        $scope.relationTypes.push(r.type);
      }
    }
    $scope.loading = false;
    $scope.colWidth = Math.min(6, Math.floor(12 / ($scope.relationTypes.length)));
    addRelationsToDict(data.relations);
  });

  termsService.get().success(function(data) {
    $scope.allTerms = data;
  });

  function addRelationsToDict(relations) {
    for (i = 0; i < relations.length; i++) {
      var r = relations[i];
      var key = r.text1.trim();
      var rObject = $scope.relationsDict[key];
      if (rObject) {
        rObject[mainTerm] = {
          term : r.term1,
          text : r.text1,
          id : r.id,
        };
        rObject[r.name] = rObject[r.name] || {
          terms : [],
          text : r.text2,
        };
        if (rObject[r.name].terms[0] && !rObject[r.name].terms[0].id) {
          rObject[r.name].terms = [];
        }
        rObject[r.name].terms.push({
          term  :r.term2,
          id : r.id,
        });
      }
    }
  }

  $scope.save = function(relation) {
    relation.saving = true;
    var data = [];
    for (var i in relation) {
      var r  = relation[i];
      if (i != mainTerm && r.terms && relation[mainTerm].term) {
        var terms = r.terms;
        for (var j = 0; j < terms.length; j++) {
          data.push({
            name : i,
            text1 : relation[mainTerm].text,
            term1 : relation[mainTerm].term,
            text2 : r.texts.join(' !! '),
            term2 : terms[j].term,
            id : terms[j].id,
          });
        }
      }
    }
    relation.alerts = [];
    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
    $http.post("relationsjson/update?source=" + source, data).success(function(data) {
      relation.alerts.push(data);
      relation.saving = false;
      relation.editting = false;
    }).error(function(data) {
      relation.alerts = relation.alerts || [];
      relation.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba.',
      });
      relation.saving = false;
    });
  };

  $scope.addField = function(relation, type) {
    if (!relation[type]) {
      relation[type] = {
        terms: [],
        texts: [],
      };
    } else if (!relation[type].terms) {
      relation[type].terms = [relation[type].term];
    }
    relation[type].terms.push({});
  };

  $scope.removeField = function(relation, type, index) {
    relation[type].terms.splice(index, 1);
  };

  $scope.closeAlert = function(relation, index) {
    relation.alerts.splice(index, 1);
  };

  $scope.alerts = [];
  $scope.exportDomain = $routeParams.exportdomain || 'anatom.cz';

  $scope.publish = function(type) {
    $scope.saving = type;
    type = type.replace(' ', '-');
    $http.get("relationsexport/" + type + '?empty=true').success(function(data) {
      exportService.export(type).success(function(data) {
        $scope.alerts.push(data);
        $scope.saving = false;
      }).error(function(data) {
        $scope.alerts.push({
          type : 'danger',
          msg : 'Na serveru nastala chyba',
        });
        $scope.saving = false;
      });
    })
    .error(function(data) {
      $scope.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba',
      });
      $scope.saving = false;
    });
  };
})

.controller('RelationsExportController',
    function($scope, $http, $routeParams, exportService) {
  $scope.loading = true;
  $scope.lang = $routeParams.lang || 'cs';
  $scope.alerts = [];
  $scope.exportDomain = $routeParams.exportdomain || 'anatom.cz';

  $http.get("relationsexport").success(function(data) {
    $scope.loading = false;
    $scope.contexts = data.contexts;
    $scope.flashcards = data.flashcards;
    $scope.terms = data.terms;
    var contextsById = {};
    angular.forEach($scope.contexts, function(c) {
      contextsById[c.id] = c;
      c.content = angular.fromJson(c.content);
    });
    var termsById = {};
    angular.forEach($scope.terms, function(t) {
      termsById[t.id] = t;
    });
    angular.forEach($scope.flashcards, function(f) {
      f.contextId = f.context;
      f.context = contextsById[f.context];
      f.term = termsById[f.term];
      f['term-secondary'] = termsById[f['term-secondary']];
      f['additional-info'] = angular.fromJson(f['additional-info']);
    });
    $scope.flashcards = $scope.flashcards.sort(function(a, b) {
      return b.term['name-cs'] - a.term['name-cs'];
    });

    $scope.setContext = function(c) {
      $scope.activeContext = c;
    };
  });

  $scope.publish = function() {
    $scope.saving = true;
    exportService.export('relations-flashcards').success(function(data) {
      $scope.alerts.push(data);
      $scope.saving = false;
    }).error(function(data) {
      $scope.alerts.push({
        type : 'danger',
        msg : 'Na serveru nastala chyba',
      });
      $scope.saving = false;
    });
  };
});
