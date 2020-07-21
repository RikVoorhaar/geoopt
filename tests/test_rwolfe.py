import sys
import geoopt
import torch
import numpy as np
import pytest


@pytest.mark.parametrize(
    "opt_params",
    [dict(), dict(c1=1e-3, c2=0.5), dict(amax=1, amin=1e-5), dict(stabilize=10)],
)
@pytest.mark.parametrize("batch_size", [None, 1, 16])
@pytest.mark.parametrize("line_search_method", ["armijo", "wolfe"])
def test_rwolfe_stiefel(opt_params, batch_size, line_search_method):
    # Use line search to solve orthogonal procrustes
    stiefel = geoopt.manifolds.Stiefel()
    torch.manual_seed(42)
    (n, m) = (10, 20)

    A = torch.randn(n, m, dtype=torch.float64)
    Q = stiefel.random((n, n), dtype=torch.float64)
    B = Q @ A

    with torch.no_grad():
        if batch_size is None:
            X = stiefel.random((n, n), dtype=torch.float64)
        else:
            X = stiefel.random((batch_size, n, n), dtype=torch.float64)
        X.requires_grad = True

    def closure():
        optim.zero_grad()
        loss = (X @ A - B).norm()
        loss.backward()
        return loss.item()

    optim = geoopt.optim.RiemannianLineSearch(
        [X], line_search_method=line_search_method, **opt_params
    )
    loss = None
    for i in range(1000):
        loss = optim.step(closure)
        if optim.last_step_size is None:
            break
    assert loss < 1e-3
