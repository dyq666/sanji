import pytest

from util import weighted_choices


def test_weighted_choices():
    a = [1, 2, 3]
    weights = [1, 2, 3]

    # 当 `k` 大于 `a` 的大小或小于 0, 会报错.
    assert len(weighted_choices(a, weights=weights, k=0)) == 0
    assert len(weighted_choices(a, weights=weights, k=1)) == 1
    assert len(weighted_choices(a, weights=weights, k=3)) == 3
    with pytest.raises(ValueError):
        weighted_choices(a, weights=weights, k=4)
    with pytest.raises(ValueError):
        weighted_choices(a, weights=weights, k=-1)

    # `weights` 必须等于 `a` 的大小, 而且相加不能为 0.
    with pytest.raises(ValueError):
        assert len(weighted_choices(a, weights=[], k=1)) == 1
    with pytest.raises(ValueError):
        assert len(weighted_choices(a, weights=[0, 0, 0], k=1)) == 1
    with pytest.raises(ValueError):
        assert len(weighted_choices(a, weights=[1, 1], k=1)) == 1
    with pytest.raises(ValueError):
        assert len(weighted_choices(a, weights=[1, 1, 1, 1], k=1)) == 1
