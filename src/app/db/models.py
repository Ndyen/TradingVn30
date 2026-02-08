from sqlalchemy import Column, Integer, String, Boolean, Numeric, TIMESTAMP, Date, ForeignKey, JSON, null
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class MarketSymbol(BaseModel):
    __tablename__ = 'market_symbol'
    __table_args__ = {'schema': 'trading'}

    symbol_id = Column(Integer, primary_key=True)
    symbol = Column(String, unique=True, nullable=False)
    exchange = Column(String, default='HOSE')
    name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True))

class Universe(BaseModel):
    __tablename__ = 'universe'
    __table_args__ = {'schema': 'trading'}

    universe_id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    source = Column(String)
    created_at = Column(TIMESTAMP(timezone=True))

class Timeframe(BaseModel):
    __tablename__ = 'timeframe'
    __table_args__ = {'schema': 'trading'}

    timeframe_id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    bar_seconds = Column(Integer)

class Strategy(BaseModel):
    __tablename__ = 'strategy'
    __table_args__ = {'schema': 'trading'}

    strategy_id = Column(Integer, primary_key=True)
    code = Column(String, unique=True)
    name = Column(String)
    description = Column(String)
    weights = Column(JSON)
    parameters = Column(JSON)
    is_active = Column(Boolean, default=True)

class UniverseMember(BaseModel):
    __tablename__ = 'universe_member'
    __table_args__ = {'schema': 'trading'}

    universe_id = Column(Integer, primary_key=True) # FK handled by DB
    symbol_id = Column(Integer, primary_key=True)   # FK handled by DB
    effective_from = Column(Date, primary_key=True)
    effective_to = Column(Date)

class OhlcvBar(BaseModel):
    __tablename__ = 'ohlcv_bar'
    __table_args__ = {'schema': 'trading'}

    symbol_id = Column(Integer, primary_key=True)
    timeframe_id = Column(Integer, primary_key=True)
    ts = Column(TIMESTAMP(timezone=True), primary_key=True)
    open = Column(Numeric(18, 4))
    high = Column(Numeric(18, 4))
    low = Column(Numeric(18, 4))
    close = Column(Numeric(18, 4))
    volume = Column(Numeric(24, 4))
    source = Column(String, default='vnstock')
    ingested_at = Column(TIMESTAMP(timezone=True))

class DataFetchLog(BaseModel):
    __tablename__ = 'data_fetch_log'
    __table_args__ = {'schema': 'trading'}

    fetch_id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer)
    timeframe_id = Column(Integer)
    requested_from = Column(TIMESTAMP(timezone=True))
    requested_to = Column(TIMESTAMP(timezone=True))
    rows_received = Column(Integer)
    cache_hit = Column(Boolean, default=False)
    status = Column(String)
    error_message = Column(String)
    duration_ms = Column(Integer)
    created_at = Column(TIMESTAMP(timezone=True))

class AnalysisRun(BaseModel):
    __tablename__ = 'analysis_run'
    __table_args__ = {'schema': 'trading'}

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    universe_id = Column(Integer)
    timeframe_id = Column(Integer)
    strategy_id = Column(Integer)
    as_of = Column(TIMESTAMP(timezone=True))
    status = Column(String, default='running')
    error_message = Column(String)
    started_at = Column(TIMESTAMP(timezone=True))
    finished_at = Column(TIMESTAMP(timezone=True))

class RunScore(BaseModel):
    __tablename__ = 'run_score'
    __table_args__ = {'schema': 'trading'}

    run_id = Column(UUID(as_uuid=True), primary_key=True)
    symbol_id = Column(Integer, primary_key=True)
    score_total = Column(Numeric(6, 2))
    score_trend = Column(Numeric(6, 2))
    score_base = Column(Numeric(6, 2))
    score_breakout = Column(Numeric(6, 2))
    score_volume = Column(Numeric(6, 2))
    score_momentum = Column(Numeric(6, 2))
    score_risk = Column(Numeric(6, 2))
    penalties = Column(JSON)
    features = Column(JSON)
    computed_at = Column(TIMESTAMP(timezone=True))

class RunSignal(BaseModel):
    __tablename__ = 'run_signal'
    __table_args__ = {'schema': 'trading'}

    run_id = Column(UUID(as_uuid=True), primary_key=True)
    symbol_id = Column(Integer, primary_key=True)
    entry_zone = Column(JSON)
    stop_loss = Column(Numeric(18, 4))
    take_profit_1 = Column(Numeric(18, 4))
    take_profit_2 = Column(Numeric(18, 4))
    invalidation = Column(JSON)
    key_reasons = Column(JSON)
    risk_notes = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True))

class RunReport(BaseModel):
    __tablename__ = 'run_report'
    __table_args__ = {'schema': 'trading'}

    run_id = Column(UUID(as_uuid=True), primary_key=True)
    top3 = Column(JSON)
    ranking = Column(JSON)
    summary = Column(JSON)
    created_at = Column(TIMESTAMP(timezone=True))
