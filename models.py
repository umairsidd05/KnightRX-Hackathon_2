from sqlalchemy import create_engine, Column, Integer, String, Date, Time, Enum, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create the SQLite database engine
DATABASE_URL = "sqlite:///knightrx.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Medication model
class Medication(Base):
    __tablename__ = 'medications'
    medication_id = Column(Integer, primary_key=True, index=True)
    med_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    total_quantity = Column(Integer, nullable=False)  # Added for refill alerts
    frequency = Column(String, nullable=False)
    reminder_time = Column(Time, nullable=False)

# Define the MedicationLog model
class MedicationLog(Base):
    __tablename__ = 'medication_logs'
    log_id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.medication_id"), nullable=False)
    date = Column(Date, default=datetime.now().date(), nullable=False)
    time = Column(Time, default=datetime.now().time(), nullable=False)
    status = Column(Enum("Taken on Time", "Taken Late", "Missed", name="status_enum"), nullable=False)

# Define the ReminderSetting model
class ReminderSetting(Base):
    __tablename__ = 'reminder_settings'
    user_id = Column(Integer, primary_key=True, index=True)
    contact_info = Column(String, nullable=False)  # Stores the user's email address

# Define the HealthCheckIn model
class HealthCheckIn(Base):
    __tablename__ = 'health_check_ins'
    check_in_id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=datetime.now().date(), nullable=False)
    symptoms = Column(Text, nullable=True)  # Stores user-entered symptoms or health notes

# Initialize the database
Base.metadata.create_all(bind=engine)
