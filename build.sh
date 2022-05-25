#!/bin/env bash

activate () {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        echo "Activating venv..."
        set -e
        source /home/user/Projects/t_rex_typer/venv/bin/activate
        echo "Activated venv"
    fi
}

build () {
    clean
    echo "Building..."
    python3 -m build
    echo "Finished building"
}

clean () {
    echo "Cleaning..."

    rm -rf build/
    if [[ ! -d "build/" ]]; then
        echo "Removed build/"
    else
        echo "[ERROR]: Failed to remove build/"
    fi

    rm -rf dist/
    if [[ ! -d "dist/" ]]; then
        echo "Removed dist/"
    else
        echo "[ERROR]: Failed to remove dist/"
    fi

    echo "Finished cleaning"
}

show_help () {
    echo "build.sh"

    echo "    help    - show this help"
    echo "    build   - build PyPi packages"
    echo "    clean   - remove build directories"
    echo "    upgrade - upgrade build environment"

}

upgrade () {
    echo "Upgrading..."
    python3 -m pip install --upgrade build
    python3 -m pip install --upgrade twine
    echo "Upgrade finished"
}

upload () {
    TWINE_USERNAME="__token__"
    python3 -m twine upload --username $TWINE_USERNAME --repository pypi dist/*
}

upload-test () {
    TWINE_USERNAME="__token__"
    python3 -m twine upload --username $TWINE_USERNAME --repository testpypi dist/*
}


if [[ $1 = "help" ]]; then
    show_help
# elif [[ $1 = "activate" ]]; then
#     activate
elif [[ $1 = "build" ]]; then
    activate
    build
elif [[ $1 = "clean" ]]; then
    clean
elif [[ $1 = "upgrade" ]]; then
    activate
    upgrade
elif [[ $1 = "upload-test" ]]; then
    activate
    upload-test
elif [[ $1 = "upload" ]]; then
    activate
    upload
else
    show_help
fi
