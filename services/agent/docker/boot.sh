#!/bin/sh
set -o errexit
set -o nounset

IFS=$(printf '\n\t')

INFO="INFO: [$(basename "$0")] "

echo "$INFO" "Booting in ${SC_BOOT_MODE} mode ..."
echo "$INFO" "User :$(id "$(whoami)")"
echo "$INFO" "Workdir : $(pwd)"

#
# DEVELOPMENT MODE
#
# - prints environ info
# - installs requirements in mounted volume
#
if [ "${SC_BUILD_TARGET}" = "development" ]; then
  echo "$INFO" "Environment :"
  printenv | sed 's/=/: /' | sed 's/^/    /' | sort
  echo "$INFO" "Python :"
  python --version | sed 's/^/    /'
  command -v python | sed 's/^/    /'

  cd services/agent
  uv pip --quiet --no-cache-dir sync requirements/dev.txt
  cd -
  echo "$INFO" "PIP :"
  uv pip list
fi

if [ "${SC_BOOT_MODE}" = "debug" ]; then
  # NOTE: production does NOT pre-installs debugpy
  uv pip install --no-cache-dir debugpy
fi

#
# RUNNING application
#
APP_LOG_LEVEL=${LOGLEVEL:-${LOG_LEVEL:-${LOGLEVEL:-INFO}}}
AGENT_SERVER_REMOTE_DEBUG_PORT=3000
SERVER_LOG_LEVEL=$(echo "${APP_LOG_LEVEL}" | tr '[:upper:]' '[:lower:]')
echo "$INFO" "Log-level app/server: $APP_LOG_LEVEL/$SERVER_LOG_LEVEL"

if [ "${SC_BOOT_MODE}" = "debug" ]; then
  reload_dir_packages=$(find /devel/packages -maxdepth 3 -type d -path "*/src/*" ! -path "*.*" -exec echo '--reload-dir {} \' \;)

  exec sh -c "
    cd services/agent/src/simcore_service_agent && \
    python -m debugpy --listen 0.0.0.0:${AGENT_SERVER_REMOTE_DEBUG_PORT} -m uvicorn main:the_app \
      --host 0.0.0.0 \
      --port 8000 \
      --reload \
      $reload_dir_packages
      --reload-dir . \
      --log-level \"${SERVER_LOG_LEVEL}\"
  "
else
  exec uvicorn simcore_service_agent.main:the_app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level "${SERVER_LOG_LEVEL}" \
    --no-access-log
fi
