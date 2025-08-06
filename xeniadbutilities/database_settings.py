class DatabaseConfiguration:
    def __init__(self, db_type, **kwargs):
        self.db_type = db_type.lower()

        if self.db_type == "postgres":
            self.username = kwargs.get("username")
            self.password = kwargs.get("password")
            self.host = kwargs.get("host", "localhost")
            self.port = kwargs.get("port", 5432)
            self.database = kwargs.get("database")
        elif self.db_type == "sqlite":
            self.file_path = kwargs.get("file_path")
        else:
            raise ValueError("Unsupported database type. Use 'postgres' or 'sqlite'.")

    def get_connection_string(self):
        if self.db_type == "postgres":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "sqlite":
            return f"sqlite:///{self.file_path}"

