
class UserNotFoundException(Exception):
    def __str__(self):
        return "Error: User not found on database"

class DisabledUserException(Exception):
    def __str__(self):
        return"Error: User has been Disabled on database"

class UserNotAdminException(Exception):
    def __str__(self):
        return "Error: User is not an admin"

class UserNotOwner(Exception):
    def __str__(self):
        return "Error: User is not the resource owner"