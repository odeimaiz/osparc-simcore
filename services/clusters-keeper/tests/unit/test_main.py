# pylint:disable=unused-variable
# pylint:disable=unused-argument
# pylint:disable=redefined-outer-name


from pytest_simcore.helpers.monkeypatch_envs import EnvVarsDict


def test_main_app(app_environment: EnvVarsDict):
    from simcore_service_clusters_keeper.main import app_factory

    app_factory()
