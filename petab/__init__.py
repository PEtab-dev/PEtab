"""PEtab global

Attributes:
    ENV_NUM_THREADS:
        Name of environment variable to set number of threads or processes
        PEtab should use for operations that can be performed in parallel.
        By default, all operations are performed sequentially.
"""

ENV_NUM_THREADS = "PETAB_NUM_THREADS"

from .calculate import *  # noqa: F403, F401, E402
from .composite_problem import *  # noqa: F403, F401, E402
from .conditions import *  # noqa: F403, F401, E402
from .core import *  # noqa: F403, F401, E402
from .lint import *  # noqa: F403, F401, E402
from .measurements import *  # noqa: F403, F401, E402
from .observables import *  # noqa: F403, F401, E402
from .parameter_mapping import *  # noqa: F403, F401, E402
from .parameters import *  # noqa: F403, F401, E402
from .problem import *  # noqa: F403, F401, E402
from .sampling import *  # noqa: F403, F401, E402
from .sbml import *  # noqa: F403, F401, E402
from .simulate import *  # noqa: F403, F401, E402
from .yaml import *  # noqa: F403, F401, E402
from .version import __version__  # noqa: F401, E402
from .format_version import __format_version__  # noqa: F401, E402
