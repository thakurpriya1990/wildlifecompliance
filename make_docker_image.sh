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
BUILD_TAG_NO_INCREMENT=dbcawa/$REPO:v$(date +%Y.%m.%d)
if [[ $# -gt 1 ]]; then
    INCREMENT=$2
else
    INCREMENT=1
    #echo "docker output"
    #echo $(docker images | awk '{print $1":"$2}' | grep $BUILD_TAG_NO_INCREMENT)
    if [[ $(docker images | awk '{print $1":"$2}' | grep $BUILD_TAG_NO_INCREMENT) ]]; then
    #if [[ $(docker images | grep $BUILD_TAG_NO_INCREMENT | awk '{print $2}') ]]; then
        #DAILY_IMAGE_INCREMENTS=$(docker images | awk '{print $1":"$2}' | grep $BUILD_TAG_NO_INCREMENT | cut -c $(${#REPO}+6)-)
        DAILY_IMAGE_INCREMENTS=$(docker images | awk '{print $1":"$2}' | grep $BUILD_TAG_NO_INCREMENT)
        declare -i I=0
        declare -A inc_array
        for DAILY in $DAILY_IMAGE_INCREMENTS;
        do
            #echo "iNC"
            #echo $DAILY
            #echo $(echo $DAILY | cut -c $((${#REPO}+21))-)
            INC=$(echo $DAILY | cut -c $((${#REPO}+21))-)
            inc_array[$I]=$INC
            #I=$(($I + 1))
            I=$(($I+1))
            #echo " this is i"
            #echo $I;
        done
        #inc_array[1]=$((3+4))
        #inc_array[2]=$((3*4))
        #inc_array[3]=$((3+1))
        #echo "inc_array"
        #echo "zero"
        #echo "${inc_array[0]}"
        #echo "one"
        #echo "${inc_array[1]}"
        #echo "two"
        #echo "${inc_array[2]}"
        #echo "three"
        #echo "${inc_array[3]}"
        #echo "length"
        #echo "${inc_array[@]}"
        #echo "max"
        #echo "${inc_array[@]}" | sort -nr | head -n1
        #echo "ifs"
        #echo $(sort <<<"${inc_array[@]}")
        declare -i max_value=0
        for ii in ${inc_array[@]};
        do
            #echo "ii"
            #echo $ii
            if [ $ii -gt $max_value ]; then
                max_value=$ii
            fi;
        done
        echo $max_value
        #echo "daily image increments"
        #echo $DAILY_IMAGE_INCREMENTS
        #exit # to remove
        INCREMENT=$((max_value+1))
    fi
fi
#BUILD_TAG=dbcawa/wildlifecompliance:v$(date +%Y.%m.%d).$1
BUILD_TAG=dbcawa/$REPO:v$(date +%Y.%m.%d).$INCREMENT
echo $INCREMENT
echo $BUILD_TAG
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
