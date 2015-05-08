"""BLAS and LAPACK access.

These functions provide access to BLAS routines from scipy which can improve
performance.  This modules is woefully incomplete - it only contains functions
that I routinely used.  It should give you an idea about how to add your own.
"""
from __future__ import absolute_import, division, print_function

__all__ = ['daxpy', 'zaxpy']

import numpy as np
from scipy.linalg import get_blas_funcs

_BLAS_ZDOTC = False


def _zdotc_no_blas(a, b):
    r"""Non-BLAS version of zdotc for use when BLAS breaks."""
    return np.dot(a.conj().ravel(), b.ravel())


def _zdotc(a, b, _zdotc=get_blas_funcs(['dotc'],
                                       [np.zeros(1, dtype=complex), ] * 2)[0]):
    a = a.ravel()
    b = b.ravel()
    assert a.flags.f_contiguous
    assert a.flags.c_contiguous
    assert _zdotc is get_blas_funcs(['dotc'], [a, b])[0]
    return _zdotc(a, b)


def _zaxpy_no_blas(y, x, a=1.0):
    r"""Non-BLAS version of zaxpy for use when BLAS breaks."""
    y += a * x
    return y


def _ddot(a, b, _ddot=get_blas_funcs(['dot'],
                                     [np.zeros(1, dtype=float), ] * 2)[0]):
    a = a.ravel()
    b = b.ravel()
    assert a.flags.f_contiguous
    assert a.flags.c_contiguous
    assert _ddot is get_blas_funcs(['dot'], [a, b])[0]
    return _ddot(a, b)


def _ddot_no_blas(a, b):
    r"""Non-BLAS version for use when BLAS breaks."""
    return np.dot(a.ravel(), b.ravel())


def _zaxpy(y, x, a=1.0,
           _axpy=get_blas_funcs(['axpy'],
                                [np.zeros(1, dtype=complex), ] * 2)[0]):
    r"""Performs ``y += a*x`` inplace using the BLAS axpy command.  This is
    significantly faster than using generic expressions that make temporary
    copies etc.

    .. note:: There is a bug in some versions of numpy that lead to segfaults
       when arrays are deallocated.  This is fixed in current versions of
       numpy, but you might need to upgrade manually.  See:

       * http://projects.scipy.org/numpy/ticket/2148
    """
    assert y.flags.c_contiguous
    assert _axpy is get_blas_funcs(['axpy'], [x, y])[0]
    return _axpy(x=x.ravel(), y=y.ravel(), n=x.size, a=a).reshape(y.shape)


def _daxpy(y, x, a=1.0,
           _axpy=get_blas_funcs(['axpy'],
                                [np.zeros(1, dtype=float), ] * 2)[0]):
    r"""Performs ``y += a*x`` inplace using the BLAS axpy command.  This is
    significantly faster than using generic expressions that make temporary
    copies etc.

    .. note:: There is a bug in some versions of numpy that lead to segfaults
       when arrays are deallocated.  This is fixed in current versions of
       numpy, but you might need to upgrade manually.  See:

       * http://projects.scipy.org/numpy/ticket/2148
    """
    assert y.flags.c_contiguous
    assert _axpy is get_blas_funcs(['axpy'], [x, y])[0]
    return _axpy(x=x.ravel(), y=y.ravel(), n=x.size, a=a).reshape(y.shape)


if _BLAS_ZDOTC:                 # pragma: nocover
    zdotc = _zdotc
    ddot = _ddot
    zaxpy = _zaxpy
    daxpy = _daxpy
else:
    ddot = _ddot_no_blas
    zdotc = _zdotc_no_blas
    zaxpy = _zaxpy_no_blas
    daxpy = _zaxpy_no_blas