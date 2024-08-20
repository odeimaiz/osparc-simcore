from collections.abc import Coroutine, Iterable
from typing import Any

import asyncpg


def find_one(
    conn: asyncpg.pool.PoolConnectionProxy,
    table: str,
    filter_: dict[str, Any],
    fields=None,
) -> Coroutine[Any, Any, asyncpg.Record | None]:
    sql, values = find_one_sql(table, filter_, fields)
    return conn.fetchrow(sql, *values)


def find_one_sql(
    table: str, filter_: dict[str, Any], fields: Iterable[str] | None = None
) -> tuple[str, list[Any]]:
    """
    >>> find_one_sql('tbl', {'foo': 10, 'bar': 'baz'})
    ('SELECT * FROM tbl WHERE bar=$1 AND foo=$2', ['baz', 10])
    >>> find_one_sql('tbl', {'id': 10}, fields=['foo', 'bar'])
    ('SELECT foo, bar FROM tbl WHERE id=$1', [10])
    """
    keys, values = _split_dict(filter_)
    fields = ", ".join(fields) if fields else "*"
    where = _pairs(keys)
    sql = f"SELECT {fields} FROM {table} WHERE {where}"  # noqa: S608 # @pcrespov SQL injection issue here
    return sql, values


def insert(
    conn: asyncpg.pool.PoolConnectionProxy,
    table: str,
    data: dict[str, Any],
    returning: str = "id",
) -> Coroutine[Any, Any, Any]:
    sql, values = insert_sql(table, data, returning)
    return conn.fetchval(sql, *values)


def insert_sql(
    table: str, data: dict[str, Any], returning: str = "id"
) -> tuple[str, list[Any]]:
    """
    >>> insert_sql('tbl', {'foo': 'bar', 'id': 1})
    ('INSERT INTO tbl (foo, id) VALUES ($1, $2) RETURNING id', ['bar', 1])

    >>> insert_sql('tbl', {'foo': 'bar', 'id': 1}, returning=None)
    ('INSERT INTO tbl (foo, id) VALUES ($1, $2)', ['bar', 1])

    >>> insert_sql('tbl', {'foo': 'bar', 'id': 1}, returning='pk')
    ('INSERT INTO tbl (foo, id) VALUES ($1, $2) RETURNING pk', ['bar', 1])
    """
    keys, values = _split_dict(data)
    sql = "INSERT INTO {} ({}) VALUES ({}){}".format(  # noqa: S608 # @pcrespov SQL injection issue here
        table,
        ", ".join(keys),
        ", ".join(_placeholders(data)),
        f" RETURNING {returning}" if returning else "",
    )
    return sql, values


def update(
    conn: asyncpg.pool.PoolConnectionProxy,
    table: str,
    filter_: dict[str, Any],
    updates: dict[str, Any],
) -> Coroutine[Any, Any, str]:
    sql, values = update_sql(table, filter_, updates)
    return conn.execute(sql, *values)


def update_sql(
    table: str, filter_: dict[str, Any], updates: dict[str, Any]
) -> tuple[str, list[Any]]:
    """
    >>> update_sql('tbl', {'foo': 'a', 'bar': 1}, {'bar': 2, 'baz': 'b'})
    ('UPDATE tbl SET bar=$1, baz=$2 WHERE bar=$3 AND foo=$4', [2, 'b', 1, 'a'])
    """
    where_keys, where_vals = _split_dict(filter_)
    up_keys, up_vals = _split_dict(updates)
    changes = _pairs(up_keys, sep=", ")
    where = _pairs(where_keys, start=len(up_keys) + 1)
    sql = f"UPDATE {table} SET {changes} WHERE {where}"  # noqa: S608 # @pcrespov SQL injection issue here
    return sql, up_vals + where_vals


def delete(
    conn: asyncpg.pool.PoolConnectionProxy, table: str, filter_: dict[str, Any]
) -> Coroutine[Any, Any, str]:
    sql, values = delete_sql(table, filter_)
    return conn.execute(sql, *values)


def delete_sql(table: str, filter_: dict[str, Any]) -> tuple[str, list[Any]]:
    """
    >>> delete_sql('tbl', {'foo': 10, 'bar': 'baz'})
    ('DELETE FROM tbl WHERE bar=$1 AND foo=$2', ['baz', 10])
    """
    keys, values = _split_dict(filter_)
    where = _pairs(keys)
    sql = f"DELETE FROM {table} WHERE {where}"  # noqa: S608 # @pcrespov SQL injection issue here
    return sql, values


def _pairs(keys: Iterable[str], *, start: int = 1, sep: str = " AND ") -> str:
    """
    >>> _pairs(['foo', 'bar', 'baz'], sep=', ')
    'foo=$1, bar=$2, baz=$3'
    >>> _pairs(['foo', 'bar', 'baz'], start=2)
    'foo=$2 AND bar=$3 AND baz=$4'
    """
    return sep.join(f"{k}=${i}" for i, k in enumerate(keys, start))


def _placeholders(variables: Iterable[Any]) -> list[Any]:
    """Returns placeholders by number of variables

    >>> _placeholders(['foo', 'bar', 1])
    ['$1', '$2', '$3']
    """
    return [f"${i}" for i, _ in enumerate(variables, 1)]


def _split_dict(dic: dict[str, Any]) -> tuple[list[str], list[Any]]:
    """Split dict into sorted keys and values

    >>> _split_dict({'b': 2, 'a': 1})
    (['a', 'b'], [1, 2])
    """
    keys = sorted(dic.keys())
    return keys, [dic[k] for k in keys]
