#!/bin/sh
set -o errexit
set -o nounset

IFS=$(printf '\n\t')

INFO="INFO: [$(basename "$0")] "
WARNING="WARNING: [$(basename "$0")] "
ERROR="ERROR: [$(basename "$0")] "

# Read self-signed SSH certificates (if applicable)
#
# In case a dynamic sidecar must access a docker registry in a secure way using
# non-standard certificates (e.g. such as self-signed certificates), this call is needed.
# It needs to be executed as root.
update-ca-certificates

# This entrypoint script:
#
# - Executes *inside* of the container upon start as --user [default root]
# - Notice that the container *starts* as --user [default root] but
#   *runs* as non-root user [scu]
#
echo "$INFO" "Entrypoint for stage ${SC_BUILD_TARGET} ..."
echo "$INFO" "User :$(id "$(whoami)")"
echo "$INFO" "Workdir : $(pwd)"
echo "$INFO" "User : $(id scu)"
echo "$INFO" "python : $(command -v python)"
echo "$INFO" "pip : $(command -v pip)"
echo "$INFO" "UV : $(command -v uv)"

#
# DEVELOPMENT MODE
# - expects docker run ... -v $(pwd):$SC_DEVEL_MOUNT
# - mounts source folders
# - deduces host's uid/gip and assigns to user within docker
#
if [ "${SC_BUILD_TARGET}" = "development" ]; then
  echo "$INFO" "development mode detected..."
  # NOTE: expects docker run ... -v $(pwd):$DEVEL_MOUNT
  DEVEL_MOUNT=/devel/services/dynamic-sidecar

  stat $DEVEL_MOUNT >/dev/null 2>&1 ||
    (echo "$ERROR" "You must mount '$DEVEL_MOUNT' to deduce user and group ids" && exit 1)

  echo "$INFO" "setting correct user id/group id..."
  HOST_USERID=$(stat --format=%u "${DEVEL_MOUNT}")
  HOST_GROUPID=$(stat --format=%g "${DEVEL_MOUNT}")
  CONT_GROUPNAME=$(getent group "${HOST_GROUPID}" | cut --delimiter=: --fields=1)
  if [ "$HOST_USERID" -eq 0 ]; then
    echo "$WARNING" "Folder mounted owned by root user... adding $SC_USER_NAME to root..."
    adduser "$SC_USER_NAME" root
  else
    echo "$INFO" "Folder mounted owned by user $HOST_USERID:$HOST_GROUPID-'$CONT_GROUPNAME'..."
    # take host's credentials in $SC_USER_NAME
    if [ -z "$CONT_GROUPNAME" ]; then
      echo "$WARNING" "Creating new group grp$SC_USER_NAME"
      CONT_GROUPNAME=grp$SC_USER_NAME
      addgroup --gid "$HOST_GROUPID" "$CONT_GROUPNAME"
    else
      echo "$INFO" "group already exists"
    fi
    echo "$INFO" "Adding $SC_USER_NAME to group $CONT_GROUPNAME..."
    adduser "$SC_USER_NAME" "$CONT_GROUPNAME"

    echo "$WARNING" "Changing ownership [this could take some time]"
    echo "$INFO" "Changing $SC_USER_NAME:$SC_USER_NAME ($SC_USER_ID:$SC_USER_ID) to $SC_USER_NAME:$CONT_GROUPNAME ($HOST_USERID:$HOST_GROUPID)"
    usermod --uid "$HOST_USERID" --gid "$HOST_GROUPID" "$SC_USER_NAME"

    echo "$INFO" "Changing group properties of files around from $SC_USER_ID to group $CONT_GROUPNAME"
    fdfind --owner ":$SC_USER_ID" --exclude proc --exec-batch chgrp --no-dereference "$CONT_GROUPNAME" . '/'
    echo "$INFO" "Changing ownership properties of files around from $SC_USER_ID to group $CONT_GROUPNAME"
    fdfind --owner "$SC_USER_ID:" --exclude proc --exec-batch chown --no-dereference "$SC_USER_NAME" . '/'
  fi
fi

# Appends docker group if socket is mounted
DOCKER_MOUNT=/var/run/docker.sock
if stat $DOCKER_MOUNT >/dev/null 2>&1; then
  echo "$INFO detected docker socket is mounted, adding user to group..."
  GROUPID=$(stat --format=%g $DOCKER_MOUNT)
  GROUPNAME=scdocker

  if ! addgroup --gid "$GROUPID" $GROUPNAME >/dev/null 2>&1; then
    echo "$WARNING docker group with $GROUPID already exists, getting group name..."
    # if group already exists in container, then reuse name
    GROUPNAME=$(getent group "${GROUPID}" | cut --delimiter=: --fields=1)
    echo "$WARNING docker group with $GROUPID has name $GROUPNAME"
  fi
  adduser "$SC_USER_NAME" "$GROUPNAME"
fi

# Change ownership of volumes mount directory
# directories are empty at this point
# each individual subdirectory is a unique volume
chown --recursive "$SC_USER_NAME":"$GROUPNAME" "${DYNAMIC_SIDECAR_DY_VOLUMES_MOUNT_DIR}"
# Allow owner and group to edit write and execute
# files from all the subdirectories
# When the service access files downloaded by the dynamic-sidecar
# it uses group permissions
chmod --recursive 774 "${DYNAMIC_SIDECAR_DY_VOLUMES_MOUNT_DIR}"

echo "$INFO Starting $* ..."
echo "  $SC_USER_NAME rights    : $(id "$SC_USER_NAME")"
echo "  local dir : $(ls -al)"
echo "  volumes dir : $(ls -al "${DYNAMIC_SIDECAR_DY_VOLUMES_MOUNT_DIR}")"

exec gosu "$SC_USER_NAME" "$@"
