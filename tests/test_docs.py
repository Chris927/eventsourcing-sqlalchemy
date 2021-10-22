# -*- coding: utf-8 -*-
import os
import sys
from pathlib import Path
from subprocess import PIPE, Popen
from tempfile import NamedTemporaryFile
from typing import List
from unittest.case import TestCase
from uuid import UUID

base_dir = Path(__file__).parents[1]


class TestExample(TestCase):
    def test(self) -> None:
        from eventsourcing.domain import Aggregate, event

        class World(Aggregate):
            def __init__(self) -> None:
                self.history: List[str] = []

            @event("SomethingHappened")
            def make_it_so(self, what: str) -> None:
                self.history.append(what)

        from eventsourcing.application import Application

        class Worlds(Application[World]):
            def create_world(self) -> UUID:
                world = World()
                self.save(world)
                return world.id

            def make_it_so(self, world_id: UUID, what: str) -> None:
                world = self.repository.get(world_id)
                world.make_it_so(what)
                self.save(world)

            def get_world_history(self, world_id: UUID) -> List[str]:
                world = self.repository.get(world_id)
                return world.history

        app = Worlds(
            env={
                "INFRASTRUCTURE_FACTORY": "eventsourcing_sqlalchemy.factory:Factory",
                "SQLALCHEMY_URL": "sqlite:///:memory:",
            }
        )
        world_id = app.create_world()
        app.make_it_so(world_id, "dinosaurs")
        app.make_it_so(world_id, "trucks")
        app.make_it_so(world_id, "internet")

        history = app.get_world_history(world_id)
        assert history == ["dinosaurs", "trucks", "internet"]


class TestDocs(TestCase):
    def tearDown(self) -> None:
        self.clean_env()

    def clean_env(self) -> None:
        keys = [
            "INFRASTRUCTURE_FACTORY",
            "SQLALCHEMY_URL",
        ]
        for key in keys:
            try:
                del os.environ[key]
            except KeyError:
                pass

    def test_readme(self) -> None:
        path = base_dir / "README.md"
        if not os.path.exists(path):
            self.skipTest("Skipped test, README file not found: {}".format(path))
        self.check_code_snippets_in_file(path)

    def check_code_snippets_in_file(self, doc_path: Path) -> None:  # noqa: C901
        lines = []
        num_code_lines = 0
        num_code_lines_in_block = 0
        is_code = False
        is_md = False
        is_rst = False
        last_line = ""
        is_literalinclude = False
        with open(doc_path) as doc_file:
            for line_index, orig_line in enumerate(doc_file):
                line = orig_line.strip("\n")
                if line.startswith("```python"):
                    # Start markdown code block.
                    if is_rst:
                        self.fail(
                            "Markdown code block found after restructured text block "
                            "in same file."
                        )
                    is_code = True
                    is_md = True
                    line = ""
                    num_code_lines_in_block = 0
                elif is_code and is_md and line.startswith("```"):
                    # Finish markdown code block.
                    if not num_code_lines_in_block:
                        self.fail(f"No lines of code in block: {line_index + 1}")
                    is_code = False
                    line = ""
                elif is_code and is_rst and line.startswith("```"):
                    # Can't finish restructured text block with markdown.
                    self.fail(
                        "Restructured text block terminated with markdown format '```'"
                    )
                elif (
                    line.startswith(".. code:: python")
                    or line.strip() == ".."
                    # and "exclude-when-testing" not in last_line
                ):
                    # Start restructured text code block.
                    if is_md:
                        self.fail(
                            "Restructured text code block found after markdown block "
                            "in same file."
                        )
                    is_code = True
                    is_rst = True
                    line = ""
                    num_code_lines_in_block = 0
                elif line.startswith(".. literalinclude::"):
                    is_literalinclude = True
                    line = ""

                elif is_literalinclude:
                    if "pyobject" in line:
                        # Assume ".. literalinclude:: ../../xxx/xx.py"
                        # Or ".. literalinclude:: ../xxx/xx.py"
                        module = last_line.strip().split(" ")[-1][:-3]
                        module = module.lstrip("./")
                        module = module.replace("/", ".")
                        # Assume "    :pyobject: xxxxxx"
                        pyobject = line.strip().split(" ")[-1]
                        statement = f"from {module} import {pyobject}"
                        line = statement
                        is_literalinclude = False

                elif is_code and is_rst and line and not line.startswith(" "):
                    # Finish restructured text code block.
                    if not num_code_lines_in_block:
                        self.fail(f"No lines of code in block: {line_index + 1}")
                    is_code = False
                    line = ""
                elif is_code:
                    # Process line in code block.
                    if is_rst:
                        # Restructured code block normally indented with four spaces.
                        if len(line.strip()):
                            if not line.startswith("    "):
                                self.fail(
                                    "Code line needs 4-char indent: {}: {}".format(
                                        repr(line), doc_path
                                    )
                                )
                            # Strip four chars of indentation.
                            line = line[4:]

                    if len(line.strip()):
                        num_code_lines_in_block += 1
                        num_code_lines += 1
                else:
                    line = ""
                lines.append(line)
                last_line = orig_line

        print("{} lines of code in {}".format(num_code_lines, doc_path))

        # Write the code into a temp file.
        tempfile = NamedTemporaryFile("w+")
        temp_path = tempfile.name
        tempfile.writelines("\n".join(lines) + "\n")
        tempfile.flush()

        # Run the code and catch errors.
        p = Popen([sys.executable, temp_path], stdout=PIPE, stderr=PIPE)
        outb, errb = p.communicate()
        out = outb.decode("utf8")
        err = errb.decode("utf8")
        out = out.replace(temp_path, str(doc_path))
        err = err.replace(temp_path, str(doc_path))
        exit_status = p.wait()

        print(out)
        print(err)

        # Check for errors running the code.
        if exit_status:
            self.fail(out + err)

        # Close (deletes) the tempfile.
        tempfile.close()
