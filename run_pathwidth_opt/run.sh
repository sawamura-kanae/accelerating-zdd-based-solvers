instance=${1}
duration=${2}

classpath="../pathwidth_opt/.build/pathwidth.jar"
classname="Pathwidth"

time="/usr/bin/time"

javaflag="-Xms1024g -Xmx1024g -Xss134m -cp ${classpath} ${classname} ${instance}"
java="java"

function main {
    local command="${time} -v timeout ${duration} ${java} ${javaflag}";

    eval ${command}
    local ret=${?}

    return ${ret};
}

main;

# vim: expandtab sts=4 sw=4
