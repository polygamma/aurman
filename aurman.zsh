#compdef aurman

#
# /usr/share/zsh/site-functions/_aurman
#

typeset -A opt_args
setopt extendedglob

# we use zstat to check ctime quickly because pacman doesn't always set
# mtime and `test 'file' -nt 'file'` uses mtime
if zmodload -F zsh/stat b:zstat 2>/dev/null; then
    # check all databases against the cache file
    function _aurman_all_packages_caching_policy() {
        [[ ! -f "$1" ]] && return 0
        for file in /var/lib/pacman/sync/*.db; do
            if [[ "$(zstat +ctime "$file")" -gt "$(zstat +ctime "$1")" ]]; then
                return 0
            fi
        done
        return 1
    }

    # check the database being completed against it's cache file
    function _aurman_repo_packages_caching_policy() {
        [[ ! -f "$1" ]] && return 0
        local file="/var/lib/pacman/sync/${words[CURRENT]%/*}.db"
        if [[ "$(zstat +ctime "$file")" -gt "$(zstat +ctime "$1")" ]]; then
            return 0
        fi
        return 1
    }
else
    # return 0 is implicit
    function _aurman_all_packages_caching_policy() {}
    function _aurman_repo_packages_caching_policy() {}
fi


# options for passing to _arguments: main aurman commands
_aurman_opts_commands=(
    ":aurman_commands:((
    {-D,--database}\:'Modify database'
    {-Q,--query}\:'Query the package database'
    {-R,--remove}\:'Remove a package from the system'
    {-S,--sync}\:'Synchronize packages'
    {-T,--deptest}\:'Check if dependencies are installed'
    {-U,--upgrade}\:'Upgrade a package'
    sync\:'Clone, build and install target(s)'
    search\:'Search AUR package names and descriptions'
    info\:'Show info for target(s)'
    buildonly\:'Clone and build target(s)'
    upgrade\:'Upgrade AUR package(s)'
    check\:'Check for AUR upgrade(s)'
    clean\:'Clean AUR package(s) and clone(s)'
    cleanall\:'Clean all AUR packages and clones'
    {-h,--help}\:'Display usage'
    '-V\:Display pacman version'
    {-v,--version}\:'Display aurman version'
    ))"
)

_aurman_opts_extended=(
    {-a,--aur}'[Only search, build, install or clean target(s) from the AUR]'
    {-e,--edit}'[Edit target(s) PKGBUILD and view install script]'
    {-r,--repo}'[Only search, build, install or clean target(s) from the repositories]'
    '--domain[Point at another domain]'
    '--foreign[Consider already installed foreign dependencies]'
    '--noedit[Do not prompt to edit files]'
    '--rebuild[Always rebuild package(s)]'
    '--silent[Silence output]'
)

# options for passing to _arguments: options common to all commands
_aurman_opts_common=(
    {-b,--dbpath}'[Alternate database location]:database_location:_files -/'
    '--color[colorize the output]:color options:(always never auto)'
    {-h,--help}'[Display syntax for the given operation]'
    '--root[Set alternate installation root]:installation root:_files -/'
    {-v,--verbose}'[Be more verbose]'
    '--cachedir[Alternate package cache location]:cache_location:_files -/'
    '--config[An alternate configuration file]:config file:_files'
    '--logfile[An alternate log file]:config file:_files'
    '--noconfirm[Do not ask for confirmation]'
    '--noprogressbar[Do not show a progress bar when downloading files]'
    '--noscriptlet[Do not execute the install scriptlet if one exists]'
    '--print[Only print the targets instead of performing the operation]'
)

# options for passing to _arguments: options for --upgrade commands
_aurman_opts_pkgfile=(
    '*-d[Skip dependency checks]'
    '*--nodeps[Skip dependency checks]'
    '--dbonly[Only remove database entry, do not remove files]'
    '--force[Overwrite conflicting files]'
    '--needed[Do not reinstall up to date packages]'
    '*:package file:_files -g "*.pkg.tar*~*.sig(.,@)"'
)

# options for passing to _arguments: subactions for --query command
_aurman_opts_query_actions=(
    '(-Q --query)'{-Q,--query}
    {-g,--groups}'[View all members of a package group]:*:package groups:->query_group'
    {-o,--owns}'[Query the package that owns a file]:file:_files'
    {-p,--file}'[Package file to query]:*:package file:->query_file'
    {-s,--search}'[Search package names and descriptions]:*:search text:->query_search'
)

# options for passing to _arguments: options for --query and subcommands
_aurman_opts_query_modifiers=(
    {-c,--changelog}'[List package changelog]'
    {-d,--deps}'[List packages installed as dependencies]'
    {-e,--explicit}'[List packages explicitly installed]'
    {\*-i,\*--info}'[View package information]'
    {\*-k,\*--check}'[Check package files]'
    {-l,--list}'[List package contents]'
    {-m,--foreign}'[List installed packages not found in sync db(s)]'
    {-n,--native}'[List installed packages found in sync db(s)]'
    {-t,--unrequired}'[List packages not required by any package]'
    {-u,--upgrades}'[List packages that can be upgraded]'
    {-q,--quiet}'[Show less information]'
)

# options for passing to _arguments: options for --remove command
_aurman_opts_remove=(
    {-c,--cascade}'[Remove all dependent packages]'
    {*-d,*--nodeps}'[Skip dependency checks]'
    {-n,--nosave}'[Remove protected configuration files]'
    {\*-s,\*--recursive}'[Remove dependencies not required by other packages]'
    '--dbonly[Only remove database entry, do not remove files]'
    '*:installed package:_aurman_completions_installed_packages'
)

_aurman_opts_database=(
    '--asdeps[mark packages as non-explicitly installed]'
    '--asexplicit[mark packages as explicitly installed]'
    '*:installed package:_aurman_completions_installed_packages'
)

# options for passing to _arguments: options for --sync command
_aurman_opts_sync_actions=(
    '(-S --sync)'{-S,--sync}
    {\*-c,\*--clean}'[Remove old packages from cache]:\*:clean:->sync_clean'
    {-g,--groups}'[View all members of a package group]:*:package groups:->sync_group'
    {-s,--search}'[Search package names and descriptions]:*:search text:->sync_search'
    '--dbonly[Only remove database entry, do not remove files]'
    '--needed[Do not reinstall up to date packages]'
    '--recursive[Reinstall all dependencies of target packages]'
)

# options for passing to _arguments: options for --sync command
_aurman_opts_sync_modifiers=(
    {\*-d,\*--nodeps}'[Skip dependency checks]'
    {\*-i,\*--info}'[View package information]'
    {-l,--list}'[List all packages in a repository]'
    {-p,--print}'[Print download URIs for each package to be installed]'
    {\*-u,\*--sysupgrade}'[Upgrade all out-of-date packages]'
    {-w,--downloadonly}'[Download packages only]'
    {\*-y,\*--refresh}'[Download fresh package databases]'
    {-q,--quiet}'[Show less information]'
    '*--ignore[Ignore a package upgrade]:package: _aurman_all_packages'
    '*--ignoregroup[Ignore a group upgrade]:package group:_aurman_completions_all_groups'
    '--asdeps[Install packages as non-explicitly installed]'
    '--asexplicit[Install packages as explicitly installed]'
    '--force[Overwrite conflicting files]'
)

# handles check subcommand
_aurman_action_check() {
    _arguments -s : \
        "*:check:(( --devel\:'Consider AUR development packages upgrade' ))"
}

# handles info subcommand
_aurman_action_info() {
   _arguments -s : \
        "$_aurman_opts_common[@]" \
        "$_aurman_opts_extended[@]" \
        "$_aurman_opts_sync_actions[@]" \
        "$_aurman_opts_sync_modifiers[@]" \
        '*:info:_aurman_completions_aur_packages'
}

# handles clean subcommand
_aurman_action_clean() {
    if [[ $AURDEST ]] then;
        CLONEDIR=$AURDEST
    elif [[ $XDG_CACHE_HOME && -a $XDG_CACHE_HOME/aurman ]]; then
        CLONEDIR=$XDG_CACHE_HOME/aurman
    else
        CLONEDIR=$HOME/.cache/aurman
    fi
    _arguments -s :  \
        "*:clean:($(ls $CLONEDIR))" \
        "$_aurman_opts_common[@]"
 }

# handles --help subcommand
_aurman_action_help() {
    _arguments -s : \
        "$_aurman_opts_commands[@]"
}

# handles cases where no subcommand has yet been given
_aurman_action_none() {
    _arguments -s : \
        "$_aurman_opts_commands[@]"
}

# handles --query subcommand
_aurman_action_query() {
    local context state line
    typeset -A opt_args

    case $state in
        query_file)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_query_modifiers[@]" \
                '*:package file:_files -g "*.pkg.tar*~*.sig(.,@)"'
            ;;
        query_group)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_query_modifiers[@]" \
                '*:groups:_aurman_completions_installed_groups'
            ;;
        query_owner)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_query_modifiers[@]" \
                '*:file:_files'
            ;;
        query_search)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_query_modifiers[@]" \
                '*:search text: '
            ;;
        *)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_query_actions[@]" \
                "$_aurman_opts_query_modifiers[@]" \
                '*:package:_aurman_completions_installed_packages'
            ;;
    esac
}

# handles --remove subcommand
_aurman_action_remove() {
    _arguments -s : \
        '(--remove -R)'{-R,--remove} \
        "$_aurman_opts_common[@]" \
        "$_aurman_opts_remove[@]"
}

# handles --database subcommand
_aurman_action_database() {
    _arguments -s : \
        '(--database -D)'{-D,--database} \
        "$_aurman_opts_common[@]" \
        "$_aurman_opts_database[@]"
}

_aurman_action_deptest () {
    _arguments -s : \
        '(--deptest)-T' \
        "$_aurman_opts_common[@]" \
        ":packages:_aurman_all_packages"
}

# handles --sync subcommand
_aurman_action_sync() {
    local context state line
    typeset -A opt_args
    if (( $+words[(r)--clean] )); then
        state=sync_clean
    elif (( $+words[(r)--groups] )); then
        state=sync_group
    elif (( $+words[(r)--search] || $+words[(r)search] )); then
        state=sync_search
    fi

    case $state in
        sync_clean)
            _arguments -s : \
                {\*-c,\*--clean}'[Remove old packages from cache]' \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_sync_modifiers[@]"
                ;;
        sync_group)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_sync_modifiers[@]" \
                '(-g --group)'{-g,--groups} \
                '*:package group:_aurman_completions_all_groups'
            ;;
        sync_search)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_sync_modifiers[@]" \
                '*:search text: '
            ;;
        *)
            _arguments -s : \
                "$_aurman_opts_common[@]" \
                "$_aurman_opts_extended[@]" \
                "$_aurman_opts_sync_actions[@]" \
                "$_aurman_opts_sync_modifiers[@]" \
                '*:packages:'$completion_repo
            ;;
    esac
}

# handles --upgrade subcommand
_aurman_action_upgrade() {
    _arguments -s : \
        '(-U --upgrade)'{-U,--upgrade} \
        "$_aurman_opts_common[@]" \
        "$_aurman_opts_pkgfile[@]"
}

# handles --version subcommand
_aurman_action_version() {
    # no further arguments
    return 0
}

# provides completions for package groups
_aurman_completions_all_groups() {
    local -a cmd groups
    _aurman_get_command
    groups=( $(_call_program groups $cmd[@] -Sg) )
    typeset -U groups
    compadd "$@" -a groups
}

# provides completions for packages available from repositories
# these can be specified as either 'package' or 'repository/package'
_aurman_completions_all_packages() {
    local curcontext="${curcontext}" cache_name repo
    local -a cmd packages repositories packages_long

    _aurman_get_command

    if compset -P1 '*/*'; then
        curcontext="${curcontext}_repo_packages"
        zstyle -s ":completion:${curcontext}:" cache-policy update_policy
        [[ -z "$update_policy" ]] && zstyle ":completion:${curcontext}:" \
            cache-policy _aurman_repo_packages_caching_policy

        repo="${words[CURRENT]%/*}"
        cache_name="pacman_repo_packages_$repo"
        if _cache_invalid "$cache_name" || ! _retrieve_cache "$cache_name"; then
            packages=( $(_call_program packages $cmd[@] -Sql "$repo") )
            typeset -U packages
            _store_cache "$cache_name" packages
        fi
        _wanted repo_packages expl "repository/package" compadd ${(@)packages}
    else
        curcontext="${curcontext}_all_packages"
        zstyle -s ":completion:${curcontext}:" cache-policy update_policy
        [[ -z "$update_policy" ]] && zstyle ":completion:${curcontext}:" \
            cache-policy _aurman_all_packages_caching_policy

        cache_name='pacman_packages'
        if _cache_invalid "$cache_name" || ! _retrieve_cache "$cache_name"; then
            packages=( $(_call_program packages $cmd[@] -Sql) )
            typeset -U packages
            _store_cache "$cache_name" packages
        fi
        _wanted packages expl "packages" compadd - "${(@)packages}"

        repositories=(${(o)${${${(M)${(f)"$(</etc/pacman.conf)"}:#\[*}/\[/}/\]/}:#options})
        typeset -U repositories
        _wanted repo_packages expl "repository/package" compadd -S "/" $repositories
    fi
}

_aurman_completions_aur_packages() {
    zstyle -T ":completion:${curcontext}:" remote-access || return 1
    local -a aur_packages
    aur_packages=($(_call_program packages cower -sq --color=never $words[CURRENT] 2>/dev/null))
    _wanted aur_packages expl "aur packages" compadd - "${(@)aur_packages}"
}

# provides completions for package groups
_aurman_completions_installed_groups() {
    local -a cmd groups
    _aurman_get_command
    groups=(${(o)${(f)"$(_call_program groups $cmd[@] -Qg)"}% *})
    typeset -U groups
    compadd "$@" -a groups
}

# provides completions for installed packages
_aurman_completions_installed_packages() {
    local -a packages
    packages_long=(/var/lib/pacman/local/*(/))
    packages=( ${${packages_long#/var/lib/pacman/local/}%-*-*} )
    compadd "$@" -a packages
}

_aurman_all_packages() {
    _alternative : \
        'localpkgs:local packages:_aurman_completions_installed_packages' \
        'aurpkgs:aur packages:_aurman_completions_aur_packages' \
        'repopkgs:repository packages:_aurman_completions_all_packages'
}

_aurman_remote_packages() {
    _alternative : \
        'aurpkgs:aur packages:_aurman_completions_aur_packages' \
        'repopkgs:repository packages:_aurman_completions_all_packages'
}

# provides completions for repository names
_aurman_completions_repositories() {
    local -a cmd repositories
    repositories=(${(o)${${${(M)${(f)"$(</etc/pacman.conf)"}:#\[*}/\[/}/\]/}:#options})
    # Uniq the array
    typeset -U repositories
    compadd "$@" -a repositories
}

# builds command for invoking pacman in a _call_program command - extracts
# relevant options already specified (config file, etc)
# $cmd must be declared by calling function
_aurman_get_command() {
    # this is mostly nicked from _perforce
    cmd=( "pacman" "2>/dev/null")
    integer i
    for (( i = 2; i < CURRENT - 1; i++ )); do
        if [[ ${words[i]} = "--config" || ${words[i]} = "--root" ]]; then
            cmd+=( ${words[i,i+1]} )
        fi
    done
}

# main dispatcher
local -a args cmds;
local tmp
args=( ${${${(M)words:#-*}#-}:#-*} )
for tmp in $words; do
    cmds+=("${${_aurman_opts_commands[(r)*$tmp\[*]%%\[*}#*\)}")
done

# handle repository filter
if [[ $words[2] != -* ]]; then
    isaur=1
else
    isaur=0
fi
if (( $+words[(r)--aur] || $+words[(r)-S*a*] || $isaur  )); then
    completion_repo='_aurman_completions_aur_packages'
elif (( $+words[(r)--repo] || $+words[(r)-S*r*] )); then
    completion_repo='_aurman_completions_all_packages'
else
    completion_repo='_aurman_remote_packages'
fi

case $args in
    h*)
        if (( ${(c)#args} <= 1 && ${(w)#cmds} <= 1 )); then
            _aurman_action_help
        else
            _message "no more arguments"
        fi
        ;;
    *h*)
        _message "no more arguments"
        ;;
    D*)
        _aurman_action_database
        ;;
    Q*g*) # ipkg groups
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_query_modifiers[@]" \
            '*:groups:_aurman_completions_installed_groups'
        ;;
    Q*o*) # file
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_query_modifiers[@]" \
            '*:package file:_files'
        ;;
    Q*p*) # file *.pkg.tar*
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_query_modifiers[@]" \
            '*:package file:_files -g "*.pkg.tar*~*.sig(.,@)"'
        ;;
    T*)
        _aurman_action_deptest
        ;;
    Q*)
        _aurman_action_query
        ;;
    R*)
        _aurman_action_remove
        ;;
    S*c*) # no completion
        _arguments -s : \
            '(-c --clean)'{\*-c,\*--clean}'[Remove all files from the cache]' \
            "$_aurman_opts_common[@]"
        ;;
    S*l*) # repos
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_sync_modifiers[@]" \
            '*:package repo:_aurman_completions_repositories' \
        ;;
    S*g*) # pkg groups
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_sync_modifiers[@]" \
            '*:package group:_aurman_completions_all_groups'
        ;;
    S*s*)
        _arguments -s : \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_sync_modifiers[@]" \
            '*:search text: '
        ;;
    S*u*)
        _arguments -s : \
            '--devel[Consider AUR development packages upgrade]' \
            "$_aurman_opts_common[@]" \
            "$_aurman_opts_extended[@]" \
            "$_aurman_opts_sync_actions[@]" \
            "$_aurman_opts_sync_modifiers[@]" \
            '*:packages:'$completion_repo
        ;;
    S*)
        _aurman_action_sync
        ;;
    T*)
         _arguments -s : \
            '-T' \
            "$_aurman_opts_common[@]" \
            ":packages:_aurman_all_packages"
        ;;
    U*)
        _aurman_action_upgrade
        ;;
    V*)
        _aurman_action_version
        ;;
    *)
        if [[ ${words[2]} != -* && ${CURRENT} -gt 2  ]] then
            case ${words[2]} in
                sync)
                    _aurman_action_sync
                    ;;
                upgrade)
                    _arguments -s : \
                        '--devel[Consider AUR development packages upgrade]' \
                        '--needed[Do not reinstall up to date packages]' \
                        "$_aurman_opts_common[@]" \
                        "$_aurman_opts_extended[@]" \
                        "$_aurman_opts_sync_modifiers[@]" \
                        '*:packages:'$completion_repo
                    ;;
                check)
                    _aurman_action_check
                    ;;
                search)
                    _aurman_action_sync
                    ;;
                info)
                    _aurman_action_info
                    ;;
                buildonly)
                    _aurman_action_sync
                    ;;
                clean)
                    _aurman_action_clean
                    ;;
                cleanall)
                    _arguments -s : \
                        "$_aurman_opts_common[@]"
                    ;;
            esac
        else
            case ${(M)words:#--*} in
                    *--help*)
                        if (( ${(w)#cmds} == 1 )); then
                            _aurman_action_help
                        else
                            return 0;
                        fi
                        ;;
                    *--version*)
                        _aurman_action_version
                        ;;
                    *--query*)
                        _aurman_action_query
                        ;;
                    *--remove*)
                        _aurman_action_remove
                        ;;
                    *--deptest*)
                        _aurman_action_deptest
                        ;;
                    *--database*)
                        _aurman_action_database
                        ;;
                    *)
                        _aurman_action_none
                        ;;
                esac
        fi
;;
esac

# vim:set ts=4 sw=2 et:
