#!/bin/bash

set -e

# http://www.ostricher.com/2014/10/the-right-way-to-get-the-directory-of-a-bash-script/
get_script_dir () {
     SOURCE="${BASH_SOURCE[0]}"
     # While $SOURCE is a symlink, resolve it
     while [ -h "$SOURCE" ]; do
          DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
          SOURCE="$( readlink "$SOURCE" )"
          # If $SOURCE was a relative symlink (so no "/" as prefix, need to resolve it relative to the symlink base directory
          [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
     done
     DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
     echo "$DIR"
}

wd=$(pwd)
sd=$(get_script_dir)

log="$HOME/.sub.log"

cd "$sd"
pipenv install

set +e
while true; do

    pipenv run python sub.py "$wd" "$@" 2> "$log"
    result="$?"
    
    if [[ "$result" == 200 ]]; then
        echo "Restart requested"
    elif [[ "$result" != 0 ]]; then
        echo "sub exited with status code $result - showing $log below"
        echo "----------------------------------------"
        cat "$log"
        exit $result
    else
        break
    fi

done
