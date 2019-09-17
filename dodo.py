import os
from pathlib import Path
from doit.action import CmdAction


def docker_compose(_targets=None):
    if _targets is None:
        _targets = []
    if isinstance(_targets, str):
        _targets = (_targets,)
    return (
        f"docker-compose"
        f" -f docker-compose.yml"
        f"{''.join([f' -f docker-compose.{target}.yml' for target in _targets])}"
    )


def execute(container, command, run=False, include=None, environment=None, **options):
    if include is None:
        include = []
    if environment is None:
        environment = []

    def sanitize_environment(word):
        return word.strip("=")

    return (
        f"{docker_compose(include)} "
        f"{'run --rm' if run else 'exec'}"
        f"{' --no-deps' if options.get('alone', False) else ''}"
        f"{''.join([f' -e {sanitize_environment(env)}' for env in environment])}"
        f" {container}"
        f" {command}"
    )


def runs_in_ci():
    return "TRAVIS" in os.environ


def container_params(remote=False, include=None, environment=None):
    if include is None:
        include = []
        if not runs_in_ci():
            include.append("override")
    if isinstance(include, str):
        include = [include]
    return [
        {
            "name": "remote",
            "long": "run",
            "inverse": "exec",
            "type": bool,
            "default": remote,
            "help": "Toggles whether docker-compose should use run, or exec",
        },
        {
            "name": "include",
            "long": "include",
            "short": "f",
            "type": list,
            "default": include,
        },
        {
            "name": "environment",
            "long": "environment",
            "short": "e",
            "type": list,
            "default": environment or [],
        },
    ]


def task_docker_compose():
    def gen_tasks():
        tasks = [
            {
                "name": "test:api:bdd",
                "container": "api",
                "command": "behave",
                "options": {},
            },
            {
                "name": "test:api:unit",
                "container": "api",
                "command": "pytest tests",
                "options": {},
            },
            {
                "name": "test:web:unit",
                "container": "web",
                "command": "yarn test",
                "options": {"alone": True},
            },
            {
                "name": "reset_database",
                "container": "api",
                "command": "/code/reset-database.sh",
                "options": {},
            },
        ]
        for task in tasks:

            def wrapper():
                # The wrapper, and kwargs is a hack to ensure that the content of task is available
                # Otherwise, the task variable (label) refer to the last item, as `run_task` is executed
                # in a different context
                kwargs = {
                    "container": task["container"],
                    "command": task["command"],
                    **task["options"],
                }

                def run_task(remote=True, include=None, environment=None):
                    return execute(
                        **kwargs, run=remote, include=include, environment=environment
                    )

                yield {
                    "basename": task["name"],
                    "actions": [CmdAction(run_task)],
                    "params": container_params(remote=True),
                    "verbosity": 2,
                }

            yield wrapper()

    yield gen_tasks()


def task_initialize_ide():
    def initialize(wip_config=False):
        from lxml import etree

        def misc_xml():
            misc_xml_path = Path(".idea/misc.xml")

            if not misc_xml_path.exists():
                with open(misc_xml_path, "a") as f:
                    f.write('<project version="4"></project>')
            with open(misc_xml_path) as f:
                misc = etree.parse(f)
            root = misc.getroot()

            def webpack_config():
                webpack_path = "$PROJECT_DIR$/web/node_modules/react-scripts/config/webpack.config.js"
                config: etree.Element = misc.find(
                    'component/[@name="WebPackConfiguration"]/option'
                )
                if config is None:
                    config = etree.Element(
                        "component", {"name": "WebPackConfiguration"}
                    )
                    config.append(
                        etree.Element("option", {"name": "path", "value": webpack_path})
                    )
                    root.append(config)
                else:
                    config.attrib["value"] = webpack_path

            webpack_config()
            misc.write(str(misc_xml_path), encoding="utf-8", pretty_print=True)

        def run_configuration(include_wip=False):
            placement = Path(".idea/runConfigurations")
            os.makedirs(placement, exist_ok=True)

            def write(name, content):
                if isinstance(content, str):
                    content = etree.fromstring(content)
                with open(placement / name, "wb") as f:
                    f.write(
                        etree.tostring(content, encoding="utf-8", pretty_print=True)
                    )
                with open(placement / ".gitignore", "a") as f:
                    f.write(name + "\n")

            for name, xml in run_configurations.items():
                if name.lower().startswith("wip"):
                    if include_wip:
                        write(name, xml)
                else:
                    write(name, xml)

        misc_xml()
        run_configuration(wip_config)

    return {
        "actions": [(initialize,)],
        "params": [
            {"name": "wip_config", "long": "wip-config", "type": bool, "default": False}
        ],
        "verbosity": 2,
    }


# flake8: noqa
run_configurations = {
    "API.xml": """<component name="ProjectRunConfigurationManager">
  <configuration default="false" name="API" type="Python.FlaskServer">
    <option name="additionalOptions" value="--host 0.0.0.0" />
    <option name="flaskDebug" value="true" />
    <module name="data-modelling-tool" />
    <option name="target" value="$PROJECT_DIR$/api/app.py" />
    <option name="targetType" value="PATH" />
    <option name="INTERPRETER_OPTIONS" value="" />
    <option name="PARENT_ENVS" value="true" />
    <option name="SDK_HOME" value="docker-compose://[$PROJECT_DIR$/docker-compose.yml, $PROJECT_DIR$/docker-compose.override.yml]:api/python" />
    <option name="WORKING_DIRECTORY" value="$PROJECT_DIR$" />
    <option name="IS_MODULE_SDK" value="false" />
    <option name="ADD_CONTENT_ROOTS" value="true" />
    <option name="ADD_SOURCE_ROOTS" value="true" />
    <EXTENSION ID="DockerComposeSettingsRunConfigurationExtension" commandLine="up" />
    <EXTENSION ID="PythonCoverageRunConfigurationExtension" runner="coverage.py" />
    <option name="launchJavascriptDebuger" value="false" />
    <method v="2" />
  </configuration>
</component>
""",
    "WEB.xml": """<component name="ProjectRunConfigurationManager">
  <configuration
     default="false"
     name="WEB"
     type="JavascriptDebugType"
     uri="http://localhost"
     useFirstLineBreakpoints="true"
   >
    <method v="2" />
  </configuration>
</component>""",
    "WIP__WEB__attach.xml": """<component name="ProjectRunConfigurationManager">
  <configuration
    default="false"
    name="WIP: WEB (attach)"
    type="ChromiumRemoteDebugType"
    factoryName="Chromium Remote"
    port="56745"
    restartOnDisconnect="true"
  >
    <method v="2" />
  </configuration>
</component>""",
    "WIP__WEB__node_.xml": """<component name="ProjectRunConfigurationManager">
  <configuration
    default="false"
    name="WIP: WEB (node)"
    type="NodeJSConfigurationType"
    application-parameters="start"
    path-to-node="docker-compose://[$PROJECT_DIR$/docker-compose.yml, $PROJECT_DIR$/docker-compose.override.yml]:web/node"
    node-parameters="--inspect-brk=&quot;0.0.0.0:9229&quot;"
    path-to-js-file="node_modules/react-scripts/bin/react-scripts.js"
    working-dir="$PROJECT_DIR$/web"
  >
    <envs>
      <env name="HOST" value="0.0.0.0" />
    </envs>
    <EXTENSION ID="com.jetbrains.nodejs.run.NodeJSStartBrowserRunConfigurationExtension">
      <browser with-js-debugger="true" />
    </EXTENSION>
    <method v="2" />
  </configuration>
</component>""",
}

if __name__ == "__main__":
    import doit

    doit.run(globals())