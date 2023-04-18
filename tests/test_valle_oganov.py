import pytest
import numpy as np
from conftest import (
    assert_n_features,
    assert_no_system_modification,
    assert_sparse,
    assert_parallellization,
    assert_symmetries,
    assert_derivatives_include,
    assert_derivatives_exclude,
    water,
)
from dscribe.descriptors import ValleOganov, MBTR


# =============================================================================
# Utilities
default_k2 = {"sigma": 10 ** (-0.625), "n": 100, "r_cut": 10}
default_k3 = {"sigma": 10 ** (-0.625), "n": 100, "r_cut": 10}


def valle_oganov(**kwargs):
    """Returns a function that can be used to create a valid ValleOganov
    descriptor for a dataset.
    """

    def func(systems=None):
        species = set()
        for system in systems:
            species.update(system.get_atomic_numbers())
        final_kwargs = {
            "species": species,
            "k2": default_k2,
            "k3": default_k3,
        }
        final_kwargs.update(kwargs)
        return ValleOganov(**final_kwargs)

    return func


# =============================================================================
# Common tests with parametrizations that may be specific to this descriptor
@pytest.mark.parametrize(
    "k2, k3, n_features",
    [
        (default_k2, None, 1 / 2 * 2 * (2 + 1) * 100),  # K2
        (None, default_k3, 1 / 2 * 2 * 2 * (2 + 1) * 100),  # K3
        (default_k2, default_k3, 1 / 2 * 2 * (2 + 1) * 100 * (1 + 2)),  # K2 + K3
    ],
)
def test_number_of_features(k2, k3, n_features):
    assert_n_features(valle_oganov(k2=k2, k3=k3), n_features)


@pytest.mark.parametrize("n_jobs", (1, 2))
@pytest.mark.parametrize("sparse", (True, False))
def test_parallellization(n_jobs, sparse):
    assert_parallellization(valle_oganov, n_jobs, sparse=sparse)


def test_no_system_modification():
    assert_no_system_modification(valle_oganov)


def test_sparse():
    assert_sparse(valle_oganov)


def test_symmetries():
    """Tests the symmetries of the descriptor."""
    assert_symmetries(valle_oganov())


@pytest.mark.parametrize("method", ("numerical",))
def test_derivatives_include(method):
    assert_derivatives_include(valle_oganov(), method)


@pytest.mark.parametrize("method", ("numerical",))
def test_derivatives_exclude(method):
    assert_derivatives_exclude(valle_oganov(), method)


# =============================================================================
# Tests that are specific to this descriptor.
def test_exceptions():
    """Tests different invalid parameters that should raise an
    exception.
    """
    # Missing r_cut
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k2={
                "sigma": 10 ** (-0.625),
                "n": 100,
            },
        )
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k3={
                "sigma": 10 ** (-0.625),
                "n": 100,
            },
        )

    # Missing n
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k2={"sigma": 10 ** (-0.625), "r_cut": 10},
        )
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k3={"sigma": 10 ** (-0.625), "r_cut": 10},
        )

    # Missing sigma
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k2={"n": 100, "r_cut": 10},
        )
    with pytest.raises(ValueError):
        ValleOganov(
            species=[1],
            k3={"n": 100, "r_cut": 10},
        )


def test_vs_mbtr():
    """Tests that the ValleOganov subclass gives the same output as MBTR with
    the corresponding parameters.
    """
    system = water()
    desc = ValleOganov(
        species=[1, 8],
        k2={"sigma": 0.1, "n": 20, "r_cut": 5},
        k3={"sigma": 0.1, "n": 20, "r_cut": 5},
    )
    feat = desc.create(system)

    desc2 = MBTR(
        species=[1, 8],
        periodic=True,
        k2={
            "geometry": {"function": "distance"},
            "grid": {"min": 0, "max": 5, "sigma": 0.1, "n": 20},
            "weighting": {"function": "inverse_square", "r_cut": 5},
        },
        k3={
            "geometry": {"function": "angle"},
            "grid": {"min": 0, "max": 180, "sigma": 0.1, "n": 20},
            "weighting": {"function": "smooth_cutoff", "r_cut": 5},
        },
        normalization="valle_oganov",
        sparse=False,
    )
    feat2 = desc2.create(system)

    assert np.array_equal(feat, feat2)