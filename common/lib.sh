#!/bin/bash

GCR_PROJECT=tigerworks-kube

clean() {
	rm -rf $SRC $BIN
}

inside_git_repo() {
	git rev-parse --is-inside-work-tree > /dev/null 2>&1
	inside_git=$?
	if [ "$inside_git" -ne 0 ]; then
		echo "Not inside a git repository"
		exit 1
	fi
}

clone() {
	if [ -x "$1" ]; then
		echo "Please specify url of repo to clone"
		exit 1
	fi
	local url="$1"
	shift
	local folder=""
	if [ "$#" -eq 1 ]; then
		folder="$1"
	fi
	local cmd="git clone $url $folder"; echo -e "\n"; echo $cmd; $cmd
}

# http://stackoverflow.com/a/36979153/244009
checkout() {
	if [ -x "$1" ]; then
		echo "Please specify which branch to checkout"
		exit 1
	fi
	inside_git_repo
	local cmd="git clean -xfd"; echo $cmd; $cmd
	cmd="git fetch --all --prune"; echo $cmd; $cmd
	cmd="git fetch --tags"; echo $cmd; $cmd
	cmd="git checkout -f -B $1 origin/$1"; echo $cmd; $cmd
}

apply_tag() {
	if [ -x "$1" ]; then
		echo "Please specify which tag to apply"
		exit 1
	fi
	inside_git_repo
	local cmd="git tag -fa $1"; echo $cmd; $cmd
	cmd="git push --tag -f"; echo $cmd; $cmd
}

# Based on metadata() func in config.py
detect_tag() {
	inside_git_repo

    # http://stackoverflow.com/a/1404862/3476121
    git_tag=$(git describe --exact-match --abbrev=0 2>/dev/null || echo '')

    commit_hash=$(git rev-parse --verify HEAD)
    git_branch=$(git rev-parse --abbrev-ref HEAD)
	commit_timestamp=$(git show -s --format=%ct)

    if [ "$git_tag" != '' ]; then
        TAG=$git_tag
        TAG_STRATEGY='git_tag'
    elif [ "$git_branch" != 'master' ] && [ "$git_branch" != 'HEAD' ]; then
        TAG=$git_branch
        TAG_STRATEGY='git_branch'
    else
		hash_ver=$(git describe --tags --always --dirty)
		TAG="${hash_ver}"
		TAG_STRATEGY='commit_hash'
    fi

    echo "TAG = $TAG"
    echo "TAG_STRATEGY = $TAG_STRATEGY"
    echo "git_tag = $git_tag"
    echo "git_branch = $git_branch"
    echo "commit_hash = $commit_hash"
    echo "commit_timestamp = $commit_timestamp"

    # write TAG info to a file so that it can be loaded by a different command or script
    if [ "$1" != '' ]; then
		cat >"$1" <<EOL
TAG=$TAG
TAG_STRATEGY=$TAG_STRATEGY
git_tag=$git_tag
git_branch=$git_branch
commit_hash=$commit_hash
commit_timestamp=$commit_timestamp
EOL
	fi
    export TAG
    export TAG_STRATEGY
    export git_tag
    export git_branch
    export commit_hash
    export commit_timestamp
}

build() {
	local cmd="docker build -t $1/$IMG:$TAG ."
	echo $cmd; $cmd
}

attic_up() {
	local cmd="docker tag $1/$2 gcr.io/$GCR_PROJECT/$2"
	echo $cmd; $cmd
	cmd="gcloud docker -- push gcr.io/$GCR_PROJECT/$2"
	echo $cmd; $cmd

	local cmd="docker tag $1/$2 docker.appscode.com/$2"
	echo $cmd; $cmd
	cmd="docker push docker.appscode.com/$2"
	echo $cmd; $cmd
}

docker_up() {
	local cmd="docker push $1/$IMG:$TAG"
	echo $cmd; $cmd

	local cmd="docker tag $1/$IMG:$TAG $1/$IMG:canary"
	echo $cmd; $cmd
	cmd="docker push $1/$IMG:canary"
	echo $cmd; $cmd
}

docker_pull() {
	local cmd="docker pull docker.appscode.com/$IMG:$TAG"
	echo $cmd; $cmd
	cmd="docker tag docker.appscode.com/$IMG:$TAG $1/$IMG:$TAG"
	echo $cmd; $cmd
}

docker_gcr() {
	local cmd="gcloud docker -- pull gcr.io/$GCR_PROJECT/$IMG:$TAG"
	echo $cmd; $cmd
	cmd="docker tag gcr.io/$GCR_PROJECT/$IMG:$TAG $1/$IMG:$TAG"
	echo $cmd; $cmd
}

docker_release() {
	local cmd="docker push $1/$IMG:$TAG"
	echo $cmd; $cmd
}

docker_check() {
	name=$IMG-$(date +%s | sha256sum | base64 | head -c 8 ; echo)
	local cmd="docker run -d -P -it --name=$name $1/$IMG:$TAG"
	echo $cmd; $cmd
	cmd="docker exec -it $name ps aux"
	echo $cmd; $cmd
	cmd="sleep 5"
	echo $cmd; $cmd
	cmd="docker exec -it $name ps aux"
	echo $cmd; $cmd
	cmd="docker stop $name && docker rm $name"
	echo $cmd; $cmd
}

docker_run() {
	img=$IMG
	if [ $# -eq 2 ]; then
		img=$2
	fi
	name=$img-$(date +%s | sha256sum | base64 | head -c 8 ; echo)
	privileged="${PRIVILEGED_CONTAINER:-}"
	net="--net=host"
	extra_opts="-v $PWD/pv:/var/pv"
	docker_cmd="${DOCKER_CMD:-}"
	echo pv > .gitignore
	mkdir -p pv
	local cmd="docker run -d -P -it $privileged $net $extra_opts --name=$name $1/$img:$TAG $docker_cmd"
	echo $cmd; $cmd
}

docker_sh() {
	img=$IMG
	if [ $# -eq 2 ]; then
		img=$2
	fi
	name=$img-$(date +%s | sha256sum | base64 | head -c 8 ; echo)
	privileged="${PRIVILEGED_CONTAINER:-}"
	net="${DOCKER_NETWORK:-}"
	extra_opts="${EXTRA_DOCKER_OPTS:-}"
	local cmd="docker run -d -P -it $privileged $net $extra_opts --name=$name $1/$img:$TAG"
	echo $cmd; $cmd
	cmd="docker exec -it $name bash"
	echo $cmd; $cmd
}

docker_rm() {
	local cmd="docker stop $(docker ps)"
	echo $cmd; $cmd
	local cmd="docker rm -f $(docker ps -a)"
	echo $cmd; $cmd
}

docker_rmi() {
	docker_rm || true
	local cmd="docker rmi -f $(docker images -a)"
	echo $cmd; $cmd
}
