from math import isclose
from typing import Union

Number = Union[float, int]

def nearly_equal(a: Number, b: Number, rel_tol: float = 1e-9, abs_tol: float = 1e-12) -> bool:
    """
     Compare two floats for near-equality.

    Args:
        a: First number.
        b: Second number.
        rel_tol: Relative tolerance (default=1e-9).
        abs_tol: Absolute tolerance (default=1e-12).

    Returns:
        True if a ≈ b within tolerances.

    Notes:
        - Use rel_tol for scale-dependent comparisons (e.g., percentages).
        - Use abs_tol for scale-independent comparisons (e.g., prices close to 0).
    """
    return isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
