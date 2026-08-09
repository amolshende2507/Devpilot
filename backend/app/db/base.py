from app.db.base_class import Base # <-- Import the actual base
from app.models.user import User # noqa
from app.models.project import Project # noqa
from app.models.repository_file import RepositoryFile # noqa
from app.models.chat_session import ChatSession # noqa <-- NEW
from app.models.chat import ChatHistory # noqa