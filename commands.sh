#!/bin/bash

conda run -n prod python main.py &
conda run -n prod python app.py