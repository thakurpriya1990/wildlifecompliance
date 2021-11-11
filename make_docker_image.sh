#!/bin/bash
cd wildlifecompliance/frontend/wildlifecompliance/ &&
npm run build &&
cd ../../../ &&
source venv/bin/activate &&
./manage_wc.py collectstatic --no-input &&
git log --pretty=medium -30 > ./wlc_git_history &&
docker image build --no-cache --tag $1 .
