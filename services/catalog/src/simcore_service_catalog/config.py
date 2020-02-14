"""

    NOTE: CONS of programmatic config
    - not testing-friendly since variables set upon import. Must reload when fixture is setup
"""
import os


def to_bool(s: str) -> bool:
    return s.lower() in ['true', '1', 'yes']


is_testing_enabled = to_bool(os.environ.get("TESTING", "true"))

# defaults in test variables
postgres_cfg = {
    'user': os.environ.get("POSTGRES_USER", "test"),
    'password': os.environ.get("POSTGRES_PASSWORD", "test"),
    'database': os.environ.get("POSTGRES_DB", "test"),
    'host':  os.environ.get("POSTGRES_HOST", "localhost"),
    'port': int(os.environ.get("POSTGRES_PORT", "5432"))
}

pg_dsn = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**postgres_cfg)
postgres_cfg = {**postgres_cfg, 'uri':pg_dsn}


app_config = {
    'host':"0.0.0.0" if "SC_BOOT_MODE" in os.environ else "127.0.0.1",
    'port':8000,
    'log_level': os.environ.get("LOGLEVEL", "debug").lower()
}


# TODO: hate globals!
app_context = {}
