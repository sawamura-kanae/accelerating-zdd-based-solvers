instance=${1}
duration=${2}

classpath="../../pathwidth_opt/.build/pathwidth.jar"
classname="Pathwidth"

javaflag="-Xms1024g -Xmx1024g -Xss134m -cp ${classpath} ${classname} ${instance}"
java="java"

function log_time {
    printf "# [date -Iseconds] "
    date -Iseconds
}

function log_stuff {
    echo "# [${1}] ${2}"
}

function main {
    local command="timeout ${duration} ${java} ${javaflag}";
    log_stuff "run" "${command}"

    log_time;

    # echo ${command}
    eval ${command}
    local ret=${?}

    log_time;

    if [ ${ret} -eq 0 ]; then
        log_stuff "ok" "${ret}"
    elif [ ${ret} -eq 124 ]; then
        log_stuff "timeout" "${ret}"
    else
        log_stuff "return code" "${ret}"
    fi

    return ${ret};
}

main;

# vim: expandtab sts=4 sw=4
