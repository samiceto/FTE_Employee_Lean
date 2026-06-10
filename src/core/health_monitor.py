"""
Component health tracking system.

Tracks the health status of all system components for monitoring and
graceful degradation decisions.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ComponentHealth(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass
class ComponentStatus:
    """Status information for a component"""
    name: str
    health: ComponentHealth
    last_check: datetime
    error_count: int = 0
    last_error: str = ""

    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'health': self.health.value,
            'last_check': self.last_check.isoformat(),
            'error_count': self.error_count,
            'last_error': self.last_error
        }


class HealthMonitor:
    """
    Tracks health status of all components.

    Provides a singleton instance for system-wide health tracking.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.components = {}
            cls._instance.status_file = Path(
                '/mnt/d/FTE_Employee/hackathon_zero/ai_employee_vault/.component_health.json'
            )
            cls._instance._load()
        return cls._instance

    def update_status(self, component: str, health: ComponentHealth, error: str = ""):
        """
        Update component health status.

        Args:
            component: Component name
            health: Health status
            error: Error message (if any)
        """
        current_status = self.components.get(component)
        error_count = current_status.error_count if current_status else 0

        if error:
            error_count += 1

        self.components[component] = ComponentStatus(
            name=component,
            health=health,
            last_check=datetime.now(),
            error_count=error_count,
            last_error=error
        )
        self._persist()
        logger.info(f"Component {component} status updated: {health.value}")

    def get_status(self, component: str) -> ComponentStatus:
        """
        Get component status.

        Args:
            component: Component name

        Returns:
            ComponentStatus for the component
        """
        return self.components.get(
            component,
            ComponentStatus(component, ComponentHealth.HEALTHY, datetime.now())
        )

    def is_healthy(self, component: str) -> bool:
        """
        Check if component is healthy.

        Args:
            component: Component name

        Returns:
            True if component is healthy
        """
        status = self.get_status(component)
        return status.health == ComponentHealth.HEALTHY

    def get_all_components(self) -> dict:
        """
        Get all component statuses.

        Returns:
            Dictionary of all component statuses
        """
        return {name: status.to_dict() for name, status in self.components.items()}

    def _persist(self):
        """Save status to disk"""
        try:
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            data = {k: v.to_dict() for k, v in self.components.items()}
            self.status_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to persist health status: {e}")

    def _load(self):
        """Load status from disk"""
        try:
            if self.status_file.exists():
                data = json.loads(self.status_file.read_text())
                for name, status_dict in data.items():
                    self.components[name] = ComponentStatus(
                        name=status_dict['name'],
                        health=ComponentHealth(status_dict['health']),
                        last_check=datetime.fromisoformat(status_dict['last_check']),
                        error_count=status_dict.get('error_count', 0),
                        last_error=status_dict.get('last_error', '')
                    )
        except Exception as e:
            logger.warning(f"Failed to load health status: {e}")
