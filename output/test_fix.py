import pytest

def divide(a, b):
    if b == 0:
        raise ValueError('Cannot divide by zero.')
    return a / b

def test_divide():
    assert divide(10, 2) == 5
    with pytest.raises(ValueError, match='Cannot divide by zero.'):
        divide(10, 0)