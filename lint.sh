function run () {
    pipenv run "$@" |& grep -v "Loading .env environment variables"
    }

    run flake8 "${1:-.}" | egrep -v '__init__.*(F401|E402)|^./app.py.*F401'
    echo =========
    run pylint --variable-rgx='(([a-z_][a-z0-9_]{1,30})|(_[a-z0-9_]*)|(__[a-z][a-z0-9_]+__))$' "${1:-app}"


