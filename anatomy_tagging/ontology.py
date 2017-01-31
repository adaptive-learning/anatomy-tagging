# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
import abc


def parse_matcher(text):
    MATCHERS = [Composition, Choice, Multiplier, Constant]
    text = text.strip()
    if '(' in text or ')' in text:
        raise ValidationError('Nested relation matchers are not supported.')
    for matcher in MATCHERS:
        parsed = matcher.parse(text, parse_matcher)
        if parsed is not None:
            return parsed
    raise ValidationError('The given relation matcher can not be parsed.')


class RelationMatcher:

    @abc.abstractmethod
    def match(self, terms, ontology):
        pass


class Constant(RelationMatcher):

    def __init__(self, relation):
        self._relation = relation

    def match(self, terms, ontology):
        return flatten_set([ontology[t].get(self._relation, set()) for t in terms])

    @staticmethod
    def parse(text, parse_fun):
        return Constant(text)

    def __str__(self):
        return self._relation


class Composition(RelationMatcher):

    def __init__(self, *chain):
        self._chain = chain

    def match(self, terms, ontology):
        for matcher in self._chain:
            terms = matcher.match(terms, ontology)
        return terms

    def __str__(self):
        return ','.join([str(c) for c in self._chain])

    @staticmethod
    def parse(text, parse_fun):
        splitted = text.split(',')
        if len(splitted) == 1:
            return None
        return Composition(*[parse_fun(s) for s in splitted])


class Choice(RelationMatcher):

    def __init__(self, *choices):
        self._choices = choices

    def match(self, terms, ontology):
        result = set()
        for choice in self._choices:
            result |= choice.match(terms, ontology)
        return result

    def __str__(self):
        return '|'.join([str(c) for c in self._choices])

    @staticmethod
    def parse(text, parse_fun):
        splitted = text.split('|')
        if len(splitted) == 1:
            return None
        return Choice(*[parse_fun(s) for s in splitted])


class Multiplier(RelationMatcher):

    def __init__(self, matcher, lower_bound=None, upper_bound=None):
        self._matcher = matcher
        self._lower_bound = 0 if lower_bound is None else lower_bound
        self._upper_bound = upper_bound

    def match(self, terms, ontology):
        counter = 0
        for _ in range(self._lower_bound):
            counter += 1
            terms = self._matcher.match(terms, ontology)
        while counter < self._upper_bound:
            new_terms = self._matcher.match(terms, ontology)
            if len(new_terms) == len(terms):
                return terms
            terms |= new_terms
            counter += 1
        return terms

    def __str__(self):
        if self._upper_bound is not None:
            return '{}*{}:{}'.format(self._matcher, self._lower_bound, self._upper_bound)
        if self._lower_bound != 0:
            return '{}*{}'.format(self._matcher, self._lower_bound)
        return '{}*'.format(self._matcher)

    @staticmethod
    def parse(text, parse_fun):
        if '*' not in text:
            return None
        splitted = text.split('*')
        if len(splitted) > 2:
            raise ValidationError('There are more than one quantifiers.')
        splitted_bounds = splitted[-1].split(':')
        upper_bound = None
        if len(splitted_bounds) == 1 and len(splitted_bounds[0]) == 0:
            lower_bound = 0
        else:
            if len(splitted_bounds) == 1:
                lower_bound = int(splitted_bounds[0])
            elif len(splitted_bounds) == 2:
                lower_bound = int(splitted_bounds[0])
                upper_bound = int(splitted_bounds[-1])
            else:
                raise ValidationError('There are more than two bounds.')
            lower_bound = int(splitted_bounds[0])
            upper_bound = int(splitted_bounds[-1])
        return Multiplier(parse_fun(splitted[0]), lower_bound=lower_bound, upper_bound=upper_bound)


def flatten_set(xxs):
    return {x for xs in xxs for x in xs}
