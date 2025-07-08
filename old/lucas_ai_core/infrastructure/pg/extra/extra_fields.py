#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@author: Nero Claudius
@date: 2025/6/11
@version: 0.0.1
"""

import re
from typing import Any

from tortoise import fields, Model


def is_integer(s: str) -> bool:
    return bool(re.fullmatch(r"^[-+]?\d+$", s))


class BigIntStrField(fields.BigIntField):
    def to_db_value(self, value: Any, instance: type[Model] | Model) -> Any:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and is_integer(value):
            return int(value)
        else:
            raise ValueError(f"value: {value} is not a valid integer.")

    def to_python_value(self, value: Any) -> Any:
        if value is None:
            return None
        return str(value)
