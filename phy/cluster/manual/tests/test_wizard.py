# -*- coding: utf-8 -*-

"""Test wizard."""

#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

from ..wizard import (_argsort,
                      _sort,
                      _next_in_list,
                      _best_clusters,
                      _wizard_group,
                      best_quality_strategy,
                      )


#------------------------------------------------------------------------------
# Test wizard
#------------------------------------------------------------------------------

def test_argsort():
    l = [(1, .1), (2, .2), (3, .3), (4, .4)]
    assert _argsort(l) == [4, 3, 2, 1]

    assert _argsort(l, n_max=0) == [4, 3, 2, 1]
    assert _argsort(l, n_max=1) == [4]
    assert _argsort(l, n_max=2) == [4, 3]
    assert _argsort(l, n_max=10) == [4, 3, 2, 1]

    assert _argsort(l, reverse=False) == [1, 2, 3, 4]


def test_sort():
    clusters = [10, 0, 1, 30, 2, 20]
               # N, i, g,  N, N,  N
    status = lambda c: ('ignored', 'good')[c] if c <= 1 else None

    assert _sort(clusters, status=status) == [10, 30, 2, 20, 1, 0]


def test_best_clusters():
    quality = lambda c: c * .1
    l = list(range(1, 5))
    assert _best_clusters(l, quality) == [4, 3, 2, 1]
    assert _best_clusters(l, quality, n_max=0) == [4, 3, 2, 1]
    assert _best_clusters(l, quality, n_max=1) == [4]
    assert _best_clusters(l, quality, n_max=2) == [4, 3]
    assert _best_clusters(l, quality, n_max=10) == [4, 3, 2, 1]


def test_next_in_list():
    l = [1, 2, 3]
    assert _next_in_list(l, 0) == 0
    assert _next_in_list(l, 1) == 2
    assert _next_in_list(l, 2) == 3
    assert _next_in_list(l, 3) == 3
    assert _next_in_list(l, 4) == 4


def test_best_quality_strategy():
    best_clusters = range(5, -1, -1)
    status = lambda c: ('ignored', 'ignored', 'good')[c] if c <= 2 else None
    similarity = lambda c, d: c + d

    def _next(selection):
        return best_quality_strategy(selection,
                                     best_clusters=best_clusters,
                                     status=status,
                                     similarity=similarity)

    assert not _next(None)
    assert not _next(())

    for i in range(5, -1, -1):
        assert _next(i) == max(0, i - 1)


def test_wizard_group():
    assert _wizard_group('noise') == 'ignored'
    assert _wizard_group('mua') == 'ignored'
    assert _wizard_group('good') == 'good'
    assert _wizard_group('unknown') is None
    assert _wizard_group(None) is None


def test_wizard_basic(mock_wizard):

    w = mock_wizard

    assert w.cluster_ids == [1, 2, 3]
    assert w.n_clusters == 3
    assert w.cluster_status(1) is None

    assert w.best_clusters() == [3, 2, 1]
    assert w.best_clusters(n_max=0) == [3, 2, 1]
    assert w.best_clusters(n_max=None) == [3, 2, 1]
    assert w.best_clusters(n_max=2) == [3, 2]
    assert w.best_clusters(n_max=1) == [3]

    assert w.most_similar_clusters(3) == [2, 1]
    assert w.most_similar_clusters(2) == [3, 1]
    assert w.most_similar_clusters(1) == [3, 2]

    assert w.most_similar_clusters(3, n_max=0) == [2, 1]
    assert w.most_similar_clusters(3, n_max=None) == [2, 1]
    assert w.most_similar_clusters(3, n_max=1) == [2]
    assert w.most_similar_clusters(3, n_max=2) == [2, 1]
    assert w.most_similar_clusters(3, n_max=10) == [2, 1]


def test_wizard_nav(mock_wizard):
    w = mock_wizard

    assert w.selection == ()

    ###
    w.selection = []
    assert w.selection == ()

    assert w.best is None
    assert w.match is None

    ###
    w.selection = [1]
    assert w.selection == (1,)

    assert w.best == 1
    assert w.match is None

    ###
    w.select([1, 2, 4])
    assert w.selection == (1, 2)

    assert w.best == 1
    assert w.match == 2

    ###
    w.previous()
    assert w.selection == (1,)

    for _ in range(2):
        w.previous()
        assert w.selection == (1,)

    ###
    w.next()
    assert w.selection == (1, 2)

    for _ in range(2):
        w.next()
        assert w.selection == (1, 2)


def test_wizard_strategy(mock_wizard):
    w = mock_wizard

    w.set_status_function(lambda x: None)

    def strategy(selection, best_clusters=None, status=None, similarity=None):
        """Return the next best cluster."""
        if not selection:
            return best_clusters[0]
        assert len(selection) == 1
        return _next_in_list(best_clusters, selection[0])

    w.set_strategy_function(strategy)
    assert w.selection == ()

    for i in range(3, 0, -1):
        w.next()
        assert w.selection == (i,)

    w.next()
    assert w.selection == (1,)
