#!/bin/bash

echo "========"
echo "Benchmark: verhulst"
echo "========"

./fptuner.py -v none -e "5e-16 1e-16 5e-17" -b "64 128" ../examples/primitives/verhulst.py


echo "========"
echo "Benchmark: sineOrder3"
echo "========"

./fptuner.py -v none -e "5e-15 1e-15 5e-16" -b "64 128" ../examples/primitives/sineOrder3.py


echo "========"
echo "Benchmark: predatorPrey"
echo "========"

./fptuner.py -v none -e "5e-16 1e-16 5e-17" -b "64 128" ../examples/primitives/predatorPrey.py


echo "========"
echo "Benchmark: cone area"
echo "========"

./fptuner.py -v none -e "1e-12 2e-13 1e-13" -b "64 128" ../examples/math/cone-area.py


echo "========"
echo "Benchmark: sine"
echo "========"

./fptuner.py -v none -e "1e-15 2e-16 1e-16" -b "64 128" ../examples/primitives/sine.py


echo "========"
echo "Benchmark: doppler 1"
echo "========"

./fptuner.py -v none -e "5e-13 1e-13 5e-14" -b "64 128" ../examples/primitives/doppler-1.py


echo "========"
echo "Benchmark: doppler 2"
echo "========"

./fptuner.py -v none -e "5e-13 1e-13 5e-14" -b "64 128" ../examples/primitives/doppler-2.py


echo "========"
echo "Benchmark: doppler 3"
echo "========"

./fptuner.py -v none -e "5e-13 1e-13 5e-14" -b "64 128" ../examples/primitives/doppler-3.py


echo "========"
echo "Benchmark: rigidBody 1"
echo "========"

./fptuner.py -v none -e "5e-13 1e-13 5e-14" -b "64 128" ../examples/primitives/rigidBody-1.py


echo "========"
echo "Benchmark: sqroot"
echo "========"

./fptuner.py -v none -e "1e-15 2e-16 1e-16" -b "64 128" ../examples/primitives/sqroot.py



echo "========"
echo "Benchmark: maxwell-boltzmann"
echo "========"

./fptuner.py -v none -e "1e-14 2e-15 1e-15" -b "64 128" ../examples/math/maxwell-boltzmann.py


echo "========"
echo "Benchmark: rigidBody 2"
echo "========"

./fptuner.py -v none -e "1e-10 2e-11 1e-11" -b "64 128" ../examples/primitives/rigidBody-2.py


echo "========"
echo "Benchmark: turbine 2"
echo "========"

./fptuner.py -v none -e "5e-14 1e-14 5e-15" -b "64 128" ../examples/primitives/turbine-2.py


echo "========"
echo "Benchmark: gaussian"
echo "========"

./fptuner.py -v none -e "1e-15 2e-16 1e-16" -b "64 128" ../examples/math/gaussian.py


echo "========"
echo "Benchmark: carbonGas"
echo "========"

./fptuner.py -v none -e "5e-08 1e-08 5e-09" -b "64 128" ../examples/primitives/carbonGas.py


echo "========"
echo "Benchmark: turbine 1"
echo "========"

./fptuner.py -v none -e "5e-14 1e-14 5e-15" -b "64 128" ../examples/primitives/turbine-1.py


echo "========"
echo "Benchmark: turbine 3"
echo "========"

./fptuner.py -v none -e "5e-14 1e-14 5e-15" -b "64 128" ../examples/primitives/turbine-3.py


echo "========"
echo "Benchmark: jet"
echo "========"

./fptuner.py -v none -e "5e-11 1e-11 5e-12" -b "64 128" ../examples/primitives/jet.py


echo "========"
echo "Benchmark: reduction"
echo "========"

./fptuner.py -v none -e "1e-12 2e-13 1e-13" -b "64 128" ../examples/micro/reduction.py
