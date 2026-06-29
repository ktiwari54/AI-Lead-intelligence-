"""Import all ORM models so SQLAlchemy metadata and mappers are fully configured."""

from backend.app.admin.models import *  # noqa: F401, F403
from backend.app.ai.models import *  # noqa: F401, F403
from backend.app.billing.models import *  # noqa: F401, F403
from backend.app.common.reference import *  # noqa: F401, F403
from backend.app.companies.models import *  # noqa: F401, F403
from backend.app.contacts.models import *  # noqa: F401, F403
from backend.app.crm.models import *  # noqa: F401, F403
from backend.app.discovery.models import *  # noqa: F401, F403
from backend.app.enrichment.models import *  # noqa: F401, F403
from backend.app.exports.models import *  # noqa: F401, F403
from backend.app.integrations.models import *  # noqa: F401, F403
from backend.app.notifications.models import *  # noqa: F401, F403
from backend.app.organizations.models import *  # noqa: F401, F403
from backend.app.search.models import *  # noqa: F401, F403
from backend.app.users.models import *  # noqa: F401, F403
from backend.app.workflows.models import *  # noqa: F401, F403
from backend.app.analytics.models import *  # noqa: F401, F403
from backend.app.platform.models import *  # noqa: F401, F403
from backend.app.security.models import *  # noqa: F401, F403