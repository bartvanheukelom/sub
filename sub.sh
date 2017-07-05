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

sd=$(get_script_dir)

# install dependencies if needed
pushd "$sd" > /dev/null
    if [[ ! -d "lib/svn-0.3.44.dist-info" ]]; then
        mkdir -p lib
        pip3 install --target=lib svn==0.3.44
    fi
popd > /dev/null

log="$HOME/.sub.log"

PYTHONPATH="$sd/lib:$PYTHONPATH" python3 "$sd/sub.py" "$@" 2> "$log"
result="$?"

if [[ "$result" != 0 ]]; then
    echo "sub exited with status code $result - showing $log below"
    echo "----------------------------------------"
    cat "$log"
fi
