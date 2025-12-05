import os
import shlex
import uuid
from pathlib import Path

from ._shell import AsyncShell
from ...toolset import ToolSet, tool
from ...utils.log import logger
from ...package_runtime.context import build_context_env


class ShellToolSet(ToolSet):
    """Shell toolset for running shell commands.

    Args:
        name: The name of the toolset.
        **kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        name: str,
        workdir: str | None = None,
        **kwargs,
    ):
        super().__init__(name, **kwargs)
        self.clientid_to_shellid = {}
        self.shells = {}
        self.workdir = (
            Path(workdir).expanduser().resolve() if workdir else Path.cwd()
        )

    def _prepare_shell_env(self) -> dict:
        return os.environ.copy()

    def _current_context_dict(self) -> dict:
        ctx = dict(self.get_context() or {})
        return ctx

    def _build_runtime_env(self) -> dict:
        return build_context_env(
            workdir=str(self.workdir),
            context_variables=self._current_context_dict(),
        )

    async def _apply_context_to_shell(self, shell: AsyncShell):
        env = self._build_runtime_env()
        if not env:
            return
        exports = " && ".join(
            f"export {key}={shlex.quote(value)}" for key, value in env.items()
        )
        try:
            await shell.run_command(exports)
        except Exception:
            logger.warning("Failed to propagate context variables to shell session")

    @tool
    async def new_shell(self) -> dict:
        """Create a new shell and return its id.
        Use `run_command_in_shell` with the returned `shell_id` to run commands."""
        shell = AsyncShell()
        shell.env = self._prepare_shell_env()
        initial_output = await shell.start()
        shell_id = str(uuid.uuid4())
        self.shells[shell_id] = shell

        # Show shell creation status
        logger.info(f"[dim]New shell created: {shell_id[:8]}[/dim]")

        return {
            "success": True,
            "shell_id": shell_id,
            "initial_output": initial_output,
        }

    @tool
    async def close_shell(self, shell_id: str) -> dict:
        """Close a shell.

        Args:
            shell_id: The id of the shell to close.
        """
        shell = self.shells.get(shell_id)
        if shell is None:
            return {"success": False, "error": "Shell not found", "shell_id": shell_id}

        await shell.close()
        del self.shells[shell_id]

        # Show shell closure status
        logger.info(f"[dim]Shell closed: {shell_id[:8]}[/dim]")
        return {"success": True, "shell_id": shell_id}

    @tool
    async def run_command_in_shell(
        self,
        shell_id: str,
        command: str | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Execute a command or fetch pending output from an existing shell.

        Args:
            shell_id: Identifier for the shell session (from `new_shell` or managed automatically by `run_command`).
            command: Command string to run. If omitted, the tool drains buffered output from the shell (e.g., after a timeout).
            timeout: Optional timeout in seconds. On timeout, the command keeps running and you can re-call this tool with
                only the shell_id to fetch remaining output.

        Returns:
            dict: Structured result including success flag, `status` ("completed" or "timeout"), and the raw output text.
        """

        shell = self.shells.get(shell_id)
        if shell is None:
            return {"success": False, "error": "Shell not found", "shell_id": shell_id}

        status = "completed"

        try:
            def _handle_timeout(message: str) -> None:
                nonlocal status, output
                status = "timeout"
                logger.info(f"[yellow]⚠️ {message}[/yellow]")
                output += "\n[Warning] The execution of the command was interrupted because of the timeout. "
                output += (
                    "You can try to run run_command_in_shell without a command to get the remaining output of the shell."
                )

            if command is not None:
                await self._apply_context_to_shell(shell)
                output, finished = await shell.run_command(command, timeout=timeout)
                if timeout is not None and not finished:
                    _handle_timeout(
                        f"Command timed out after {timeout}s - call run_command_in_shell without a command to fetch remaining output"
                    )
            else:
                output, finished = await shell.read_until_marker(timeout=timeout)
                if timeout is not None and not finished:
                    _handle_timeout(
                        f"Reading shell output timed out after {timeout}s"
                    )
        except Exception as exc:
            return {"success": False, "error": str(exc), "shell_id": shell_id}

        response = {
            "success": True,
            "shell_id": shell_id,
            "status": status,
            "output": output,
        }
        if command is not None:
            response["command"] = command
        return response

    def _is_shell_alive(self, shell_id: str) -> bool:
        """Check if a shell is still alive and responsive."""
        if shell_id not in self.shells:
            return False

        shell = self.shells[shell_id]
        if not shell.process:
            return False

        # Check if process is still running
        if shell.process.returncode is not None:
            return False

        return True

    async def _restart_shell(self, client_id: str) -> str:
        """Restart a shell for a given client_id."""
        old_shell_id = self.clientid_to_shellid.get(client_id)

        # Clean up old shell if it exists
        if old_shell_id and old_shell_id in self.shells:
            try:
                await self.close_shell(old_shell_id)
            except Exception:
                pass  # Ignore cleanup errors
            finally:
                if old_shell_id in self.shells:
                    del self.shells[old_shell_id]

        # Create new shell
        logger.warning(f"Shell crashed (client_id: {client_id}), restarting...")
        res = await self.new_shell()
        new_shell_id = res["shell_id"]
        self.clientid_to_shellid[client_id] = new_shell_id
        logger.info(f"Shell restarted (client_id: {client_id})")

        return new_shell_id

    @tool
    async def run_command(
        self,
        command: str,
        timeout: int | None = None,
    ):
        """Run shell command and return a structured result.

        Args:
            command: The command to run.
            timeout: Optional timeout. Use None for long-running commands.
        """
        context_dict = dict(self.get_context() or {})
        client_id = context_dict.get("client_id")
        if client_id is None:
            client_id = "default"
            logger.warning("No client id provided, using default client id.")

        initial_output = ""
        shell_id = self.clientid_to_shellid.get(client_id)

        # Check if we need to create a new shell
        if (shell_id is None) or (shell_id not in self.shells):
            res = await self.new_shell()
            shell_id = res["shell_id"]
            initial_output = res["initial_output"]
            self.clientid_to_shellid[client_id] = shell_id

        # Check if shell is still alive before running command
        if not self._is_shell_alive(shell_id):
            shell_id = await self._restart_shell(client_id)
            initial_output = ""  # New shell will have its own initial output

        result = await self.run_command_in_shell(
            shell_id=shell_id,
            command=command,
            timeout=timeout,
        )

        # If the shell crashed, restart it but do not rerun the command automatically
        if not result.get("success") and self._should_restart(result.get("error")):
            logger.warning(
                f"Shell command failed for shell {shell_id[:8]}: {result.get('error')}"
            )
            shell_id = await self._restart_shell(client_id)
            return result

        if not result.get("success"):
            return result

        if initial_output and result.get("success"):
            combined_output = result.get("output") or ""
            result["output"] = (
                f"{initial_output}\n{combined_output}" if combined_output else initial_output
            )

        return result

    def _should_restart(self, error_message: str | None) -> bool:
        if not error_message:
            return False
        error_msg = error_message.lower()
        return any(
            keyword in error_msg
            for keyword in ["broken", "closed", "process", "pipe", "not found"]
        )

    async def run_setup(self):
        """Setup the toolset before running it."""
        logger.warning(
            "This ToolSet is not secure, it can be used to execute arbitrary code."
            " Please be careful when using it."
            " Highly recommend using it in a controlled environment like a docker container."
        )
