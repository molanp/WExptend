class RouteRegistrationError(Exception):
    def __init__(self, route_name, existing_file, duplicate_file):
        super().__init__(
            f"Route '{route_name}' is already registered.\n"
            f"Original: {existing_file}\n"
            f"Duplicate: {duplicate_file}"
        )
        self.route_name = route_name
        self.existing_file = existing_file
        self.duplicate_file = duplicate_file
