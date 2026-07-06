from database import engine, SessionLocal
from models import Base, Video
import uuid

def test_database_connection():
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Insert test video
    db = SessionLocal()
    test_video = Video(
        id=uuid.uuid4(),
        title="Test Video",
        instructor_id=uuid.uuid4(),
        file_path="/tmp/test.mp4"
    )
    db.add(test_video)
    db.commit()

    # Query test video
    retrieved = db.query(Video).filter(Video.title == "Test Video").first()
    assert retrieved is not None
    assert retrieved.title == "Test Video"

    db.close()
    print("✓ Database connection and ORM models working")

if __name__ == "__main__":
    test_database_connection()
