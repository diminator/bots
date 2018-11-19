#!/bin/sh

az container create \
    --resource-group slack-bot-maestro \
    --name maestrobot-instance-0 \
    --image maestrobot.azurecr.io/botrepo/maestro:v1 \
    --restart-policy OnFailure \
    --environment-variables 'SPOTIFY_USER'=${SPOTIFY_USER} 'SPOTIFY_CLIENT_ID'=${SPOTIFY_CLIENT_ID} 'SPOTIFY_CLIENT_SECRET'=${SPOTIFY_CLIENT_SECRET} 'SLACK_BOT_TOKEN_maestro'=${SLACK_BOT_TOKEN_maestro} 'SLACK_BOT_NAME'=${SLACK_BOT_NAME}
