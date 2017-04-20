#!/bin/bash

source_repo() {
	RETVAL=0

	if [ $# -eq 0 ]; then
		cmd=${DEFAULT_COMMAND:-build}
		$cmd
		exit $RETVAL
	fi

	case "$1" in
		build)
			build k8sdb
			;;
		build_binary)
			build_binary
			;;
		build_docker)
			build_docker
			;;
		clean)
			clean
			;;
		push)
			docker_up k8sdb $IMG:$TAG
			;;
		pull)
			docker_pull k8sdb
			;;
		gcr)
			docker_gcr k8sdb
			;;
		release)
			docker_release k8sdb
			;;
		check)
			docker_check k8sdb
			;;
		run)
			docker_run k8sdb
			;;
		sh)
			docker_sh k8sdb
			;;
		rm)
			docker_rm
			;;
		rmi)
			docker_rmi
			;;
		*)	(10)
			echo $"Usage: $0 {build|build_binary|build_docker|clean|push|pull|release|check|sh|rm|rmi}"
			RETVAL=1
	esac
	exit $RETVAL
}

binary_repo() {
	RETVAL=0

	if [ $# -eq 0 ]; then
		cmd=${DEFAULT_COMMAND:-build}
		$cmd
		exit $RETVAL
	fi

	case "$1" in
		build)
			build k8sdb
			;;
		clean)
			clean
			;;
		push)
			docker_up k8sdb $IMG:$TAG
			;;
		pull)
			docker_pull k8sdb
			;;
		gcr)
			docker_gcr k8sdb
			;;
		release)
			docker_release k8sdb
			;;
		check)
			docker_check k8sdb
			;;
		run)
			docker_run k8sdb
			;;
		sh)
			docker_sh k8sdb
			;;
		rm)
			docker_rm
			;;
		rmi)
			docker_rmi
			;;
		*)	(10)
			echo $"Usage: $0 {build|clean|push|pull|release|check|sh|rm|rmi}"
			RETVAL=1
	esac
	exit $RETVAL
}
