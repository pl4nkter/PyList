import threading
import time
import re
import os
from datetime import datetime, timedelta
from plyer.utils import platform
from plyer import notification


def format_time(t: datetime) -> str:
    return t.strftime("%Y-%m-%d %I:%M:%S %p %Z%z")


def parse_time(time_str: str) -> timedelta:
    time_units = {"d": "days", "h": "hours", "m": "minutes", "s": "seconds"}
    time_pattern = re.compile(r'(\d+)([dhms])')

    kwargs = {}
    for amount, unit in time_pattern.findall(time_str):
        if unit in time_units:
            kwargs[time_units[unit]] = int(amount)

    return timedelta(**kwargs)


def convert_timedelta(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")

    # Combine parts with commas and 'and'
    if len(parts) > 1:
        readable_time = ', '.join(parts[:-1]) + ', and ' + parts[-1]
        # readable_time = ', '.join(parts)
    elif parts:
        readable_time = parts[0]
    else:
        readable_time = "0 seconds"

    return readable_time


class TodoList:
    def __init__(self):
        self._list = {}

    def list(self) -> {}:
        return self._list

    def add(self, name: str, description: str, time_str: str) -> None:
        now = datetime.now()
        delta = parse_time(time_str)

        self._list[name] = {"description": description, "start": now, "deadline": now + delta}

        print(f'Added "{name}" to the list.')

    def remove(self, name: str) -> None:
        if name in self._list:
            self._list.pop(name, None)
            print(f'Removed "{name}" from the list.')
        else:
            raise ValueError(f"Task '{name}' not found.")

    def snooze(self, name: str, time_str: str) -> None:
        if name in self._list:
            delta = parse_time(time_str)
            self._list[name]["deadline"] += delta

            print(f'Snoozed "{name}".')
        else:
            raise ValueError(f"Task '{name}' not found.")

    def get_task(self, name: str) -> str:
        if name in self._list:
            return self._list[name]
        else:
            raise ValueError(f"Task '{name}' not found.")

    def get_description(self, name: str) -> str:
        if name in self._list:
            return self._list[name].get("description")
        else:
            raise ValueError(f"Task '{name}' not found.")

    def get_deadline(self, name: str) -> datetime:
        if name in self._list:
            return self._list[name].get("deadline")
        else:
            raise ValueError(f"Task '{name}' not found.")

    def get_start(self, name: str) -> datetime:
        if name in self._list:
            return self._list[name].get("start")
        else:
            raise ValueError(f"Task '{name}' not found.")

    def time_left(self, name: str) -> timedelta:
        if name in self._list:
            deadline = self._list[name]["deadline"]
            now = datetime.now()

            return deadline - now
        else:
            raise ValueError(f"Task '{name}' not found.")

    def print(self) -> None:
        sorted_tasks = sorted(self._list.items(), key=lambda item: item[1]["deadline"])

        if not self._list:
            print("The list is empty.")
            return

        print("-" * 40)

        for task_name, task_info in sorted_tasks:
            description = task_info["description"]
            start = format_time(task_info["start"])
            deadline = format_time(task_info["deadline"])
            time_left = convert_timedelta(self.time_left(task_name))

            print(f"Task: {task_name.capitalize()}")
            print(f"  Description:  {description}")
            print(f"  Start:        {start}")
            print(f"  Deadline:     {deadline}")
            print(f"  Time left:    {time_left}")
            print("-" * 40)

        print(f"  Current time: {format_time(datetime.now())}")

    def check_due_tasks(self) -> []:
        now = datetime.now()
        due_tasks = [name for name, info in self._list.items() if info['deadline'] <= now]

        return due_tasks

    def alert_due_tasks(self) -> None:
        due_tasks = self.check_due_tasks()

        for name in due_tasks:
            description = self.get_description(name)
            start = format_time(self.get_start(name))
            deadline = format_time(self.get_deadline(name))

            notification.notify(
                app_name="PyList",
                app_icon=os.path.join(os.path.dirname(__file__), 'icon.{}'.format(
                    'ico' if platform == 'win' else 'png')
                                      ),
                title=f"Task Due: {name.capitalize()}",
                message=f"Description: {description}\nDeadline: {deadline}",
            )

            print(f"\nAlert: Task '{name}' is due now!")
            print(f"  Description: {description}")
            print(f"  Start:       {start}")
            print(f"  Deadline:    {deadline}")
            print("-" * 40)

            self.remove(name)

    @staticmethod
    def help() -> None:
        print("""
Available commands:
    add <name> <time> <description>
        Aliases: create, new
        Description: Add a new task with a specified time and description.
        Example: add dishes 5h30m wash the dishes

    snooze <name> <time>
        Aliases: delay
        Description: Snooze an existing task by a specified amount of time.
        Example: snooze chores 2h30m

    remove <name>
        Aliases: delete, rm, del
        Description: Remove a task from the list.
        Example: remove homework

    list
        Aliases: ls, show
        Description: List all tasks sorted by their due time.
        
    clear
        Aliases: cls
        Description: Clears the console.

    help
        Aliases: cmd, cmds
        Description: Show this help message.

    exit
        Aliases: quit
        Description: Exit the application.

Time Format:
    - The time argument can be given in any order without spaces.
    - Use 'd' for days, 'h' for hours, 'm' for minutes, and 's' for seconds.
    - Examples: 2h30m, 1d5h, 10s, 2d7m, 2h
""")


def alert_thread(todo) -> None:
    while True:
        todo.alert_due_tasks()
        time.sleep(1)


def main() -> None:
    todo = TodoList()

    print("PyList")
    todo.help()

    threading.Thread(target=alert_thread, args=(todo,), daemon=True).start()

    command_aliases = {
        "add": ["add", "create", "new"],
        "remove": ["remove", "delete", "rm", "del"],
        "snooze": ["snooze", "delay"],
        "list": ["list", "ls", "show"],
        "clear": ["clear", "cls"],
        "help": ["help", "cmd", "cmds"],
        "exit": ["exit", "quit"]
    }

    while True:
        user_input = input("# ").strip().lower()

        parts = user_input.split(maxsplit=1)
        if not parts:
            continue

        base_command = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        command = None
        for cmd, aliases in command_aliases.items():
            if base_command in aliases:
                command = cmd
                break

        if command == "add":
            if args:
                parts = args.split(maxsplit=2)
                if len(parts) < 3:
                    print("Error: Command must include a name, time, and description.")
                    continue

                name = parts[0]
                time_str = parts[1]
                description = parts[2]
                todo.add(name, description, time_str)
            else:
                print("Error: Command must include a name, time, and description.")

        elif command == "remove":
            if args:
                name = args
                todo.remove(name)
            else:
                print("Error: Command must include a name.")

        elif command == "snooze":
            if args:
                parts = args.split(maxsplit=1)
                if len(parts) < 2:
                    print("Error: Command must include a name and time.")
                    continue

                name = parts[0]
                time_str = parts[1]
                todo.snooze(name, time_str)
            else:
                print("Error: Command must include a name and time.")

        elif command == "list":
            todo.print()

        elif command == "clear":
            os.system('cls')

        elif command == "help":
            todo.help()

        elif command == "exit":
            print("Exiting application.")
            break

        else:
            print("Unknown command. Type 'help' for a list of commands.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
