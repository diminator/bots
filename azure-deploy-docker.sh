#!/bin/sh
docker build -t ${MAESTRO_DOCKER_TAG} .

docker login --username maestrobot --password ${AZ_CONTAINER_REPO} maestrobot.azurecr.io
docker tag ${MAESTRO_DOCKER_TAG} maestrobot.azurecr.io/botrepo/${MAESTRO_DOCKER_TAG}
docker push maestrobot.azurecr.io/botrepo/${MAESTRO_DOCKER_TAG}

az container create \
    --resource-group slack-bot-maestro \
    --name maestrobot-instance-0 \
    --image maestrobot.azurecr.io/botrepo/${MAESTRO_DOCKER_TAG} \
    --restart-policy OnFailure \
    --environment-variables 'SPOTIFY_USER'=${SPOTIFY_USER} 'SPOTIFY_CLIENT_ID'=${SPOTIFY_CLIENT_ID} 'SPOTIFY_CLIENT_SECRET'=${SPOTIFY_CLIENT_SECRET} 'SLACK_BOT_TOKEN_maestro'=${SLACK_BOT_TOKEN_maestro} 'SLACK_BOT_NAME'=${SLACK_BOT_NAME}
