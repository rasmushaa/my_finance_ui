"""Domain model for authenticated frontend users."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """Represent an authenticated user session in the UI layer.

    Attributes
    ----------
    user_name : str
        Display name returned by the backend after Google authentication.
    user_picture_url : str
        URL to the user's profile image.
    user_role : str
        UI role used to enable or disable admin-only pages.
    encoded_jwt_token : str
        JWT token used in ``Authorization`` headers for backend API requests.
    """

    user_name: str
    user_picture_url: str
    user_role: str
    encoded_jwt_token: str

    @property
    def token(self) -> str:
        """Return the JWT token used for API authentication.

        Returns
        -------
        str
            Encoded JWT token from the authenticated session.
        """
        return self.encoded_jwt_token

    @property
    def role(self) -> str:
        """Return the UI role of the current user.

        Returns
        -------
        str
            Role label used by page navigation logic.
        """
        return self.user_role

    def is_logged_in(self) -> bool:
        """Check whether the user has a non-empty authentication token.

        Returns
        -------
        bool
            ``True`` when the user token is present, otherwise ``False``.
        """
        return bool(self.token)

    def is_admin(self) -> bool:
        """Check whether the user has administrator privileges in the UI.

        Returns
        -------
        bool
            ``True`` for admin users, otherwise ``False``.
        """
        return self.role == "admin"
