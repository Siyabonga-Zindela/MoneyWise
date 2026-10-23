"""All ORM models for the user's backend half (10 tables).

NOTE for the team: the partner's 11 tables (risk engine, FSCA, products, ...)
intentionally have NO models yet. Do NOT run `alembic revision --autogenerate`
until the partner's models exist too - autogenerate would emit DROP statements
for tables missing from the metadata. Write manual migrations instead.
"""

from .audit_log import AuditLog
from .educational_resource import EducationalResource
from .login_attempt import LoginAttempt
from .privacy_request import PrivacyRequest
from .refresh_token import RefreshToken
from .role import Role
from .scam_report import ScamReport
from .scam_report_review import ScamReportReview
from .user import User
from .user_role import UserRole

__all__ = [
    "AuditLog",
    "EducationalResource",
    "LoginAttempt",
    "PrivacyRequest",
    "RefreshToken",
    "Role",
    "ScamReport",
    "ScamReportReview",
    "User",
    "UserRole",
]
