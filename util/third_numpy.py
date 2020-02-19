__all__ = (
    'weighted_choices',
)

from fractions import Fraction
from typing import List, Union

import numpy as np

Num = Union[int, float]


def weighted_choices(population: list, weights: List[Num],
                     k: int = 1) -> list:
    """无 replace 的权重随机.

    此外:
      - 如果想用有 replace 的权重随机, 使用 `random.choices`.
      - 如果想用无 replace 的随机, 使用 `random.sample`.
      - 如果想用有 replace 的随机, 使用 `random.choices`.
    """
    acount = sum(weights)
    if not acount:
        raise ValueError

    weight_list = [Fraction(w, acount) for w in weights]
    r = np.random.choice(population, size=k, replace=False, p=weight_list)
    return list(r)
