#!/bin/bash
## first parameter is DBCA branch name

set -e
if [[ $# -lt 1 ]]; then
    echo "ERROR: DBCA branch must be specified"
    echo "$0 1"
    exit 1
fi

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
#REPO=$(basename -s .git `git config --get remote.origin.url` | sed 's/-//g')
REPO=$(awk '{split($0, arr, "\/"); print arr[2]}' <<< $(git config -l|grep remote|grep url|head -n 1|sed 's/-//g'|sed 's/....$//'))
BUILD_TAG=dbcawa/$REPO:$1_v$(date +%Y.%m.%d.%H.%M%S)
DBCA_ORIGIN_HASH=$(echo "$REPO" | md5sum -t | cut -c1-32)
DBCA_BRANCH="$DBCA_ORIGIN_HASH_"$1
EXISTING_REMOTES=$(git remote)

{
    if (( ! $(grep -c "$EXISTING_REMOTES" <<< "$DBCA_ORIGIN_HASH") )); then
        echo "Attempt to create branch"
        echo $REPO
        echo "git remote add $DBCA_ORIGIN_HASH git@github.com:dbca-wa/$REPO.git"
        git remote add $DBCA_ORIGIN_HASH git@github.com:dbca-wa/$REPO.git
        git remote set-url --push $DBCA_ORIGIN_HASH no_push
        git checkout -b $DBCA_ORIGIN_HASH_compliance_mgt_dev $DBCA_ORIGIN_HASH/compliance_mgt_dev
    fi
} ||
{
    echo "ERROR: Failed to create dbca branch"
    echo "$0 1"
    exit 1
}

{
    git checkout $DBCA_BRANCH
} ||
{
    #echo "ERROR: You must have your local code checked in and the DBCA branch set up on local with the 'dbca_' prefix.  Example Instructions:"
    #echo "git remote add dbca git@github.com:dbca-wa/wildlifecompliance.git"
    #echo "git checkout -b dbca_compliance_mgt_dev dbca/compliance_mgt_dev"

    echo "ERROR: Failed to checkout dbca branch"
    echo "$0 1"
    exit 1
}

{
    git pull &&
    cd $REPO/frontend/$REPO/ &&
    # Apply front end venv if it exists
    { 
        source venv/bin/activate && npm run build 
    } || 
    { 
        npm run build
        echo "INFO: Front end built without venv"
    }
    cd ../../../ &&
    source venv/bin/activate &&
    python manage_wc.py collectstatic --no-input &&
    git log --pretty=medium -30 > ./git_history_recent &&
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
{
    docker push $BUILD_TAG
} || {
    git checkout $CURRENT_BRANCH
    echo "ERROR: Docker push failed"
    echo "$0 1"
    exit 1
}
