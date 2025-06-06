"""Configurações centralizadas do projeto."""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()


@dataclass
class ModelConfig:
    """Configurações do modelo LLM."""
    name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "llama3"))
    temperature: float = field(default_factory=lambda: float(os.getenv("MODEL_TEMPERATURE", "0.1")))
    top_p: float = field(default_factory=lambda: float(os.getenv("MODEL_TOP_P", "0.9")))
    num_predict: int = field(default_factory=lambda: int(os.getenv("MODEL_NUM_PREDICT", "2048")))


@dataclass
class DatabaseConfig:
    """Configurações do banco de dados."""
    uri: str = field(default_factory=lambda: os.getenv("DATABASE_URI", "sqlite:///sus_data.db"))
    sample_rows: int = field(default_factory=lambda: int(os.getenv("SAMPLE_ROWS", "3")))


@dataclass
class AgentConfig:
    """Configurações do agente SQL."""
    max_iterations: int = field(default_factory=lambda: int(os.getenv("MAX_ITERATIONS", "10")))
    verbose: bool = field(default_factory=lambda: os.getenv("VERBOSE", "False").lower() == "true")
    handle_parsing_errors: bool = True


@dataclass
class AppConfig:
    """Configuração principal da aplicação."""
    model: ModelConfig = field(default_factory=ModelConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    def __post_init__(self):
        """Validações pós-inicialização."""
        if self.model.temperature < 0 or self.model.temperature > 1:
            raise ValueError("Temperature deve estar entre 0 e 1")

        if self.agent.max_iterations <= 0:
            raise ValueError("Max iterations deve ser maior que 0")


# Instância global de configuração
config = AppConfig()