#!/bin/bash
## first parameter is DBCA branch name, optional second parameter is an integer indicating incremental daily version
if [[ $# -lt 1 ]]; then
    echo "ERROR: DBCA branch must be specified"
    echo "$0 1"
    exit 1
fi
if [[ $# -gt 1 ]] && ! [[ $2 =~ ^[0-9]+$ ]]; then
    #echo "ERROR: Must specify integer indicating incremental daily version e.g."
    echo "ERROR: Incremental daily version must be an integer"
    echo "$0 1"
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
REPO=$(basename -s .git `git config --get remote.origin.url` | sed 's/-//g')
DBCA_BRANCH="dbca_"$1

BUILD_TAG_NO_VERSION=dbcawa/$REPO:v$(date +%Y.%m.%d)
#EXISTING_DOCKER_IMAGES=$(docker images | grep "wildlifecompliance" | awk '{print $2}' | cut -c 3-)
VERSION=0
if [[ $(docker images | grep $BUILD_TAG_NO_VERSION) ]]; then
    DAILY_IMAGE_VERSIONS=$(docker images | grep $BUILD_TAG_NO_VERSION | awk '{print $2}' | cut -c 12-)
    echo "daily image versions"
    echo $DAILY_IMAGE_VERSIONS
else
    $VERSION=1
fi
#BUILD_TAG=dbcawa/wildlifecompliance:v$(date +%Y.%m.%d).$1
BUILD_TAG=dbcawa/$REPO:v$(date +%Y.%m.%d).$VERSION

{
    #git checkout dbca_compliance_mgt_dev
    git checkout $DBCA_BRANCH
} ||
{
    echo "ERROR: You must have the DBCA branch set up on local with the 'dbca_' prefix.  Example Instructions:"
    echo "git remote add dbca git@github.com:dbca-wa/wildlifecompliance.git"
    echo "git checkout -b dbca_compliance_mgt_dev dbca/compliance_mgt_dev"
    echo "$0 1"
    exit 1
}
{
    git pull &&
    cd $REPO/frontend/$REPO/ &&
    npm run build &&
    cd ../../../ &&
    source venv/bin/activate &&
    ./manage_wc.py collectstatic --no-input &&
    git log --pretty=medium -30 > ./wlc_git_history &&
    docker image build --no-cache --tag $BUILD_TAG . &&
    git checkout $CURRENT_BRANCH
    echo $BUILD_TAG
} ||
{
    git checkout $CURRENT_BRANCH
    echo "ERROR: Docker build failed"
    echo "$0 1"
    exit 1
}
    docker push $BUILD_TAG
} || {
    git checkout $CURRENT_BRANCH
    echo "ERROR: Docker push failed"
    echo "$0 1"
    exit 1
}
