#!/usr/bin/env bash
# Try the above env first, if that doesn't work then
# delete these first four lines and use the line below
# instead.
#!/usr/bin/bash
# Or try: #!/bin/bash on Mac
# set -xe # Enable debugging of each command
# Run using either `docker.sh start` or `docker.sh stop`

# Key configuration parameters are set in config.sh -- this
# makes it easy for us to set up new projects with minimal
# effort: change the config file instead of the startup/shutdown
# script.
if [[ $2 ]]; then
	if [[ $2 == *.sh ]]; then
		echo "Using configuration details from $2"
		. $2
	else
		echo "Using configuration details from $2.sh"
		. "$2.sh"
	fi
else
	echo "Using default configuration from config.sh."
	. ./config.sh
fi

# Container runtime detection (prefer podman, fallback to docker)
CONTAINER_CLI="podman"
if ! command -v podman >/dev/null 2>&1; then
	if command -v docker >/dev/null 2>&1; then
		CONTAINER_CLI="docker"
	else
		echo "Error: Neither podman nor docker command found." >&2
		exit 1
	fi
fi

err_report() {
	printf "Container runtime has shut down the '%s' container...\n" "$DOCKER_NM"
}

# For information about styling outputs, see this nice overview:
#  https://askubuntu.com/a/985386
if [[ $1 == "start" ]]; then
	# Try to deal with issues relating to the operating system
	# in which Docker/Podman is running. 
	WIN_CMD=""
	if [[ $OSTYPE == "msys" ]]; then
		WIN_CMD="winpty"
	fi

	# Architecture detection
	ARCH="$(uname -m)"
	if [[ "$ARCH" == "arm64" || "$ARCH" == "aarch64" ]]; then
		TARGET_ARCH="arm64"
	else
		TARGET_ARCH="amd64"
	fi

	# Resolve image tag: if single-arch tag exists locally, prefer it; otherwise use base (multi-arch manifest)
	if "$CONTAINER_CLI" image exists "${DOCKER_IMG}-${TARGET_ARCH}" 2>/dev/null || "$CONTAINER_CLI" image inspect "${DOCKER_IMG}-${TARGET_ARCH}" >/dev/null 2>&1; then
		DOCKER_IMG="${DOCKER_IMG}-${TARGET_ARCH}"
	fi

	printf "Using container runtime \e[1m%s\e[0m with image \e[1m%s\e[0m...\n" "$CONTAINER_CLI" "$DOCKER_IMG"

	# Rootless Linux & SELinux volume options
	EXTRA_FLAGS=()
	VOL_SUFFIX=""
	if [[ "$CONTAINER_CLI" == "podman" ]]; then
		VOL_SUFFIX=":z"
		# On native Linux rootless podman, keep-id maps host user to jovyan (UID 1000)
		if [[ "$OSTYPE" == "linux"* ]]; then
			IS_ROOTLESS=$("$CONTAINER_CLI" info --format '{{.Host.Security.Rootless}}' 2>/dev/null || echo "false")
			if [[ "$IS_ROOTLESS" == "true" ]]; then
				EXTRA_FLAGS+=("--userns=keep-id:uid=1000,gid=100")
			fi
		fi
	fi

	PLATFORM=""
	if [[ $(uname -p) == 'arm' && "$TARGET_ARCH" == "amd64" ]]; then
		PLATFORM="--platform linux/amd64"
	fi

	DASK_CMD=()
	if [[ ${DASK_PORT:+x} ]]; then
		 DASK_CMD=("-p" "${DASK_PORT}:8787")
	fi
	QUARTO_CMD=()
	if [[ ${QUARTO_PORT:+x} ]]; then
		printf "Run \e[1;4mquarto preview --host 0.0.0.0 --port ${QUARTO_PORT}\e[0m to use Quarto.\n"
		QUARTO_CMD=("-p" "${QUARTO_PORT}:${QUARTO_PORT}")
	fi
	NETWORK_CMD=()
	if [[ ${DOCKER_NET:+x} ]]; then
		NETWORK_CMD=("--net" "${DOCKER_NET}")
	fi
	# Create local extension directories to ensure
	# that container daemon doesn't do it with root ownership.
	mkdir -p "$HOME/.vscode/containers/$DOCKER_NM-extensions"
	mkdir -p "$HOME/.vscode/containers/$DOCKER_NM-insiders"

	# And all systems go!
	CONTAINER_ID=$(${WIN_CMD} "$CONTAINER_CLI" run --rm -d --name "$DOCKER_NM" \
		${PLATFORM} \
		"${NETWORK_CMD[@]}" \
		"${EXTRA_FLAGS[@]}" \
		-p "$JUPYTER_PORT":8888 \
		"${DASK_CMD[@]}" \
		"${QUARTO_CMD[@]}" \
		-v "$WORK_DIR:/home/jovyan/work${VOL_SUFFIX}" \
		-v "$HOME/.vscode/containers/$DOCKER_NM-extensions:/home/jovyan/.vscode-server/extensions${VOL_SUFFIX}" \
		-v "$HOME/.vscode/containers/$DOCKER_NM-insiders:/home/jovyan/.vscode-server-insiders${VOL_SUFFIX}" \
		"$DOCKER_IMG" start.sh jupyter lab \
		--LabApp.password="$JUPYTER_PWD" \
		--ServerApp.password="$JUPYTER_PWD" \
		--NotebookApp.token="$NOTEBOOK_TOKEN")

	URL="localhost:${JUPYTER_PORT}/lab/tree/work"
	DIR="$(basename "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" && echo x)"
	DIR="${DIR%x}"
	
	if [[ $DIR == $DOCKER_NM ]]; then
		URL="$URL/$DOCKER_NM"
	fi

	printf "Server \e[3mshould\e[0m soon be available on: "
	printf "\e[1;4;48:2::71:160:71m\e]8;;http://$URL\e\\$URL\e]8;;\e\\"
	printf "\e[0m\n"
	echo "Container id: $CONTAINER_ID"
elif [[ $1 == "stop" ]]; then
	echo "Shutting down..."
	CONTAINER=$("$CONTAINER_CLI" ps -aq -f "name=^/${DOCKER_NM}$|name=^${DOCKER_NM}$")
	if [[ -n "$CONTAINER" ]]; then
		"$CONTAINER_CLI" kill --signal=SIGINT $CONTAINER >/dev/null 2>&1 || true
		sleep 2
		"$CONTAINER_CLI" rm -f $CONTAINER >/dev/null 2>&1 || true
		printf "Container '%s' has now been shut down.\n" "$DOCKER_NM"
	else
		printf "No running container named '%s' found.\n" "$DOCKER_NM"
	fi
else
	printf "You need to pass either \e[1;4mstart\e[0m or \e[1;4mstop\e[0m to this script.\n"
fi
