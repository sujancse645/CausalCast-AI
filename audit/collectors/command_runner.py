import subprocess
import time
import sys
from typing import Optional, List, Union
from audit.schemas.evidence import CommandEvidence
from audit.collectors.secret_redactor import redact_secrets

def run_command(command: Union[str, List[str]], timeout: Optional[float] = None) -> CommandEvidence:
    """Runs a command, captures output, redacts secrets, and returns structured evidence."""
    start_time = time.time()
    
    is_string_cmd = isinstance(command, str)
    # Use shell on Windows if running a string command
    shell = sys.platform.startswith("win") and is_string_cmd
    
    try:
        result = subprocess.run(
            command,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        stdout = redact_secrets(result.stdout)
        stderr = redact_secrets(result.stderr)
        returncode = result.returncode
        timeout_reached = False
    except subprocess.TimeoutExpired as e:
        stdout = redact_secrets(e.stdout.decode('utf-8', errors='replace') if e.stdout else "")
        stderr = redact_secrets(e.stderr.decode('utf-8', errors='replace') if e.stderr else "")
        returncode = -1
        timeout_reached = True
    except Exception as e:
        stdout = ""
        stderr = str(e)
        returncode = -1
        timeout_reached = False
        
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    
    cmd_str = command if isinstance(command, str) else " ".join(command)
    
    return CommandEvidence(
        command=cmd_str,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        execution_time_ms=execution_time_ms,
        timeout_reached=timeout_reached
    )
