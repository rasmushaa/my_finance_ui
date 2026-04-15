
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    """ Represents a user in the system. 
    
    This is used for authentication and authorization purposes.
    
    Attributes
    ----------
    user_name: str
        The display name of the user from google auth, used for display purposes in the UI.
    user_picture_url: str
        The profile image url of the user from google auth, used for display purposes in the UI.
    user_role: str
        The role of the user, either 'admin' or 'user', used to dynamically control access to certain features.
        Note: this UI role is only used for the UI, and does not affect the backend API access control, which is handled separately in the backend.
    encoded_jwt_token: str
        A JWT token for the user, used for authentication purposes in the backend API.
    """
    user_name: str
    user_picture_url: str
    user_role: str
    encoded_jwt_token: str

    @property
    def token(self) -> str:
        """ Get the JWT token of the user. 
        
        Returns
        -------
        str
            The JWT token of the user.
        """
        return self.encoded_jwt_token

    @property
    def role(self) -> str:
        """ Get the role of the user. 
        
        Returns
        -------
        str
            The role of the user, either 'admin' or 'user'.
        """
        return self.user_role
    
    def is_logged_in(self) -> bool:
        """ Check if the user is logged in by checking if the token is not empty. 
        
        Returns
        -------
        bool
            True if the user is logged in, False otherwise.
        """
        return self.token != ''
    
    def is_admin(self) -> bool:
        """ Check if the user is an admin by checking if the role is 'admin'. 
        
        Returns
        -------
        bool
            True if the user is an admin, False otherwise.
        """
        return self.role == 'admin'