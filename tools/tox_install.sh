#!/usr/bin/env bash

# Constraint file contains this package version pin that is in conflict
# with installing the package from source. We should replace the version pin in
# the constraints file before applying it for from-source installation.

function install_dependencies() {
    local changes=$(echo $1 | tr '^' ' ')
    local change
    local project
    local ref
    local dir

    if [ -n "$changes" ]; then
        echo -e "\tAnalyzing changes $changes"
        for change in $changes; do
            project=$(echo $change | cut -d: -f1);
            if [ "$project" = "$ZUUL_PROJECT" ]; then
                echo -e "\tSkip the change: $change"
            else
                echo -e "\tFetching change: $change."
                ref=$(echo $change | cut -d: -f3);
                dir=/opt/git/$(basename $project)
                $ZUUL_CLONER --cache-dir \
                    /opt/git \
                    git://git.openstack.org \
                    $project
                pushd $dir
                if git fetch $ZUUL_URL/$project $ref; then
                    git merge FETCH_HEAD
                fi
                popd
                edit-constraint $localfile -- $project "-e git+file://$dir"
            fi
        done
    else
        edit-constraints $localfile -- "python-monascaclient" \
            "-e git+http://github.com/openstack/python-monascaclient@master#egg=python-monascaclient"
    fi
}

ZUUL_CLONER=/usr/zuul-env/bin/zuul-cloner
BRANCH_NAME=master
PACKAGE_NAME=monasca-ui
requirements_installed=$(echo "import openstack_requirements" | python 2>/dev/null ; echo $?)

set -e

git config --global url.https://git.openstack.org/.insteadOf git://git.openstack.org/

CONSTRAINTS_FILE=$1
shift

install_cmd="pip install"
mydir=$(mktemp -dt "$PACKAGE_NAME-tox_install-XXXXXXX")
trap "rm -rf $mydir" EXIT
localfile=$mydir/upper-constraints.txt
if [[ $CONSTRAINTS_FILE != http* ]]; then
    CONSTRAINTS_FILE=file://$CONSTRAINTS_FILE
fi
curl $CONSTRAINTS_FILE -k -o $localfile
install_cmd="$install_cmd -c$localfile"

if [ $requirements_installed -eq 0 ]; then
    echo "ALREADY INSTALLED" > /tmp/tox_install.txt
    echo "Requirements already installed; using existing package"
elif [ -x "$ZUUL_CLONER" ]; then
    echo "ZUUL CLONER" > /tmp/tox_install.txt
    pushd $mydir
    $ZUUL_CLONER --cache-dir \
        /opt/git \
        --branch $BRANCH_NAME \
        git://git.openstack.org \
        openstack/requirements
    cd openstack/requirements
    $install_cmd -e .
    popd
else
    echo "PIP HARDCODE" > /tmp/tox_install.txt
    if [ -z "$REQUIREMENTS_PIP_LOCATION" ]; then
        REQUIREMENTS_PIP_LOCATION="git+https://git.openstack.org/openstack/requirements@$BRANCH_NAME#egg=requirements"
    fi
    $install_cmd -U -e ${REQUIREMENTS_PIP_LOCATION}
fi

# This is the main purpose of the script: Allow local installation of
# the current repo. It is listed in constraints file and thus any
# install will be constrained and we need to unconstrain it.
edit-constraints $localfile -- $PACKAGE_NAME "-e file://$PWD#egg=$PACKAGE_NAME"
install_dependencies ${ZUUL_CHANGES:-''}

$install_cmd -U $*
exit $?
