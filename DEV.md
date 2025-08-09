## Project bootstrap
install python version 3.10 <br>
install depedencies from Pipfile/Pipfile.lock <br>
sync with dev deps, like: `pipenv sync -dev`

copy koop_form/env_temp to koop_form/.env and provide local envs

use koop_form/manage.py for runserver command, like: <br>
`python koop_form/manage.py runserver`

### Tests:
run `pytest` from koop_form/

