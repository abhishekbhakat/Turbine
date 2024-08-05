from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

from . import airflow, delete, farm


class TurbineShell:
    def __init__(self):
        self.commands = {
            "init_farm": farm.get_or_create_farm,
            "create_project": self.create_project,
            "start_project": self.start_project,
            "stop_project": self.stop_project,
            "delete_project": delete.delete_proj,
            "delete_farm": delete.delete_farm,
            "list_projects": self.list_projects,
            "exit": self.exit,
        }
        self.completer = WordCompleter(list(self.commands.keys()))
        self.style = Style.from_dict({
            "prompt": "ansicyan bold",
        })
        self.session = PromptSession(completer=self.completer, style=self.style)

    def run(self):
        print("Welcome to Turbine Interactive Shell. Type 'exit' to quit.")
        while True:
            try:
                command = self.session.prompt("Turbine> ")
                if command in self.commands:
                    self.commands[command]()
                else:
                    print(f"Unknown command: {command}")
            except KeyboardInterrupt:
                continue
            except EOFError:
                break

    def create_project(self):
        # Implement interactive project creation here
        pass

    def start_project(self):
        # Implement interactive project start here
        pass

    def stop_project(self):
        # Implement interactive project stop here
        pass

    def list_projects(self):
        projects = airflow.get_all_projects()
        if projects:
            print("Created Airflow projects:")
            for project in projects:
                print(f"- {project}")
        else:
            print("No Airflow projects found.")

    def cli_exit(self):
        print("Goodbye!")
        raise EOFError


def main():
    shell = TurbineShell()
    shell.run()


if __name__ == "__main__":
    main()
