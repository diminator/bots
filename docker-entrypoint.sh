#!/bin/sh

export CONFIG_FILE=/chatbots/config.ini
envsubst < /chatbots/config.ini.template > /chatbots/config.ini
python chatbots/run.py
tail -f /dev/null
