from sqlalchemy import inspect, text

from db.database import engine


def migrate_document_metadata():
    inspector = inspect(engine)

    if "documents" not in inspector.get_table_names():
        print("Documents table does not exist. Run database initialization first.")
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("documents")
    }

    migrations = {
        "content_hash": "ALTER TABLE documents ADD COLUMN content_hash VARCHAR(64)",
        "document_version": "ALTER TABLE documents ADD COLUMN document_version INTEGER NOT NULL DEFAULT 1",
        "index_version": "ALTER TABLE documents ADD COLUMN index_version VARCHAR(100)",
    }

    with engine.begin() as connection:
        existing_indexes = {
            index["name"]
            for index in inspect(connection).get_indexes("documents")
        }
        
        if "ix_documents_content_hash" not in existing_indexes:
            connection.execute(
                text(
                    "CREATE INDEX ix_documents_content_hash "
                    "ON documents (content_hash)"
                )
            )
            print("Created index: ix_documents_content_hash")
        else:
            print("Index already exists: ix_documents_content_hash")
        
        for column_name, migration_sql in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(migration_sql))
                print(f"Added column: {column_name}")
            else:
                print(f"Column already exists: {column_name}")

    print("Document metadata migration completed.")


if __name__ == "__main__":
    migrate_document_metadata()