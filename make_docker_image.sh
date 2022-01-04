#!/bin/bash
## sole parameter is an integer indicating incremental daily version
BUILD_TAG=dbcawa/wildlifecompliance:v$(date +%Y.%m.%d).$1
git checkout dbca_compliance_mgt_dev &&
git pull &&
cd wildlifecompliance/frontend/wildlifecompliance/ &&
npm run build &&
cd ../../../ &&
source venv/bin/activate &&
./manage_wc.py collectstatic --no-input &&
git log --pretty=medium -30 > ./wlc_git_history &&
docker image build --no-cache --tag $BUILD_TAG . &&
git checkout working
echo $BUILD_TAG &&
docker push $BUILD_TAG
