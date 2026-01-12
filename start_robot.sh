#!/bin/bash

echo "Aguardando rede..."
sleep 10

cd /home/luk/robot

echo "Iniciando Olhos..."
sudo python3 eyes.py &

echo "Iniciando Ouvidos..."
./client &

wait