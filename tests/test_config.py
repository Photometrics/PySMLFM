#!/usr/bin/env python3

import pkgutil
from dataclasses import fields

import pytest

import smlfm


@pytest.mark.parametrize(
    "indents",
    (
        pytest.param(None),
        pytest.param(1),
        pytest.param(4),
    ),
)
def test_config(indents):
    cfg1_dump = pkgutil.get_data(
        smlfm.__name__, 'data/default-config.json').decode()
    cfg1 = smlfm.Config.from_json(cfg1_dump)

    # Deserialization should result in exactly same data types and values
    cfg2_dump = cfg1.to_json(indent=indents)
    cfg2 = smlfm.Config.from_json(cfg2_dump)
    for field in fields(smlfm.Config):
        cfg1_val = getattr(cfg1, field.name)
        cfg2_val = getattr(cfg2, field.name)
        msg = (f'{field.name} (type {field.type}): '
               f'"{cfg1_val}" (type {type(cfg1_val)}) != '
               f'"{cfg2_val}" (type {type(cfg2_val)})')
        if cfg1_val != cfg2_val:
            raise ValueError(f'Value mismatch: {msg}')
        if type(cfg1_val) is not type(cfg2_val):
            raise TypeError(f'Type mismatch: {msg}')
