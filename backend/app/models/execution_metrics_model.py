from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ExecutionMetrics(Base):
    __tablename__ = "execution_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # 🔗 Node
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)

    # 🧠 Script identity
    task_id = Column(String, nullable=True)
    script_id = Column(String, nullable=True)
    language = Column(String, nullable=False)
    script_content = Column(String, nullable=True)

    # 📜 Script features
    file_size = Column(Float)
    line_count = Column(Integer)
    imports = Column(Integer)
    functions = Column(Integer)
    classes = Column(Integer)

    # 🖥 Node features
    cpu_cores = Column(Integer)
    total_memory = Column(Float)
    cpu_frequency = Column(Float)

    # 📊 Runtime metrics
    cpu_avg = Column(Float)
    cpu_peak = Column(Float)
    memory_avg = Column(Float)
    memory_peak = Column(Float)
    temperature_avg = Column(Float)

    # ⏱ Execution result
    execution_time = Column(Float, nullable=False)

    # 🎯 Target
    composite_score = Column(Float)

    # 🕒 Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)

    node = relationship("Node")
