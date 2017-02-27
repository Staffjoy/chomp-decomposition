#!/bin/bash
set -e

python -c "from chomp import Tasking; t = Tasking(); t.server()"
exit 1
