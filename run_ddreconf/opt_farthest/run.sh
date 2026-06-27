col=${1}
dat=${2}
duration=${3}

elf="../../ddreconf/ddreconf"
time="/usr/bin/time"

function main {
    local command="${time} -v timeout ${duration} ${elf} ${col} --stfile=${dat} --tj --indset --longest"
    eval ${command}
}

main;

# vim: expandtab sts=4 sw=4
