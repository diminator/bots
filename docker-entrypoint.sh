#!/bin/sh

export CONFIG_FILE=bots/config.ini
envsubst < /config.ini.template > /config.ini
python chatbots/run.py
tail -f /dev/null
