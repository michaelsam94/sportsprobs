"""Probability model configuration service with JSON storage."""

import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import logging

from app.application.dto.probability_config_dto import (
    ProbabilityConfigDTO,
    ProbabilityConfigCreateDTO,
    ProbabilityConfigUpdateDTO,
    ModelWeightsDTO,
    ThresholdsDTO,
    FeatureFlagsDTO,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProbabilityConfigService:
    """Service for managing probability model configurations."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration service.

        Args:
            config_file: Path to JSON config file (default: config/probability_models.json)
        """
        if config_file is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
            config_dir.mkdir(exist_ok=True)
            config_file = str(config_dir / "probability_models.json")
        
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, ProbabilityConfigDTO] = {}
        self._load_configs()

    def _load_configs(self):
        """Load configurations from JSON file."""
        if not self.config_file.exists():
            logger.info(f"Config file not found: {self.config_file}. Creating default.")
            self._create_default_config()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._configs = {}
            for version, config_data in data.get('configurations', {}).items():
                try:
                    # Parse datetime strings
                    if 'created_at' in config_data and config_data['created_at']:
                        config_data['created_at'] = datetime.fromisoformat(config_data['created_at'])
                    if 'updated_at' in config_data and config_data['updated_at']:
                        config_data['updated_at'] = datetime.fromisoformat(config_data['updated_at'])
                    
                    self._configs[version] = ProbabilityConfigDTO(**config_data)
                except Exception as e:
                    logger.error(f"Error loading config version {version}: {e}")
                    continue

            logger.info(f"Loaded {len(self._configs)} configuration(s) from {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            self._create_default_config()

    def _save_configs(self):
        """Save configurations to JSON file."""
        try:
            data = {
                'metadata': {
                    'last_updated': datetime.utcnow().isoformat(),
                    'total_configurations': len(self._configs),
                },
                'configurations': {}
            }

            for version, config in self._configs.items():
                config_dict = config.model_dump()
                # Convert datetime to ISO format
                if config_dict.get('created_at'):
                    config_dict['created_at'] = config_dict['created_at'].isoformat()
                if config_dict.get('updated_at'):
                    config_dict['updated_at'] = config_dict['updated_at'].isoformat()
                data['configurations'][version] = config_dict

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._configs)} configuration(s) to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
            raise

    def _create_default_config(self):
        """Create default configuration."""
        default_config = ProbabilityConfigCreateDTO(
            version="1.0.0",
            description="Default probability model configuration",
            is_active=True,
        )
        self.create_config(default_config)
        logger.info("Created default configuration")

    def get_config(self, version: Optional[str] = None) -> Optional[ProbabilityConfigDTO]:
        """Get configuration by version or active configuration.

        Args:
            version: Configuration version (None = get active config)

        Returns:
            Configuration DTO or None
        """
        if version:
            return self._configs.get(version)
        
        # Get active configuration
        for config in self._configs.values():
            if config.is_active:
                return config
        
        # If no active config, return latest version
        if self._configs:
            latest = max(self._configs.values(), key=lambda c: c.version)
            return latest
        
        return None

    def get_all_configs(self) -> List[ProbabilityConfigDTO]:
        """Get all configurations.

        Returns:
            List of configuration DTOs
        """
        return list(self._configs.values())

    def create_config(self, config_data: ProbabilityConfigCreateDTO) -> ProbabilityConfigDTO:
        """Create a new configuration.

        Args:
            config_data: Configuration data

        Returns:
            Created configuration DTO

        Raises:
            ValueError: If version already exists
        """
        if config_data.version in self._configs:
            raise ValueError(f"Configuration version {config_data.version} already exists")

        # Merge with defaults
        model_weights = config_data.model_weights or ModelWeightsDTO()
        thresholds = config_data.thresholds or ThresholdsDTO()
        feature_flags = config_data.feature_flags or FeatureFlagsDTO()

        # Create new config
        new_config = ProbabilityConfigDTO(
            version=config_data.version,
            model_weights=model_weights,
            thresholds=thresholds,
            feature_flags=feature_flags,
            description=config_data.description,
            is_active=config_data.is_active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # If this is set as active, deactivate others
        if new_config.is_active:
            for config in self._configs.values():
                config.is_active = False

        self._configs[new_config.version] = new_config
        self._save_configs()

        logger.info(f"Created configuration version {new_config.version}")
        return new_config

    def update_config(
        self,
        version: str,
        config_data: ProbabilityConfigUpdateDTO,
    ) -> ProbabilityConfigDTO:
        """Update an existing configuration.

        Args:
            version: Configuration version
            config_data: Update data

        Returns:
            Updated configuration DTO

        Raises:
            ValueError: If version doesn't exist
        """
        if version not in self._configs:
            raise ValueError(f"Configuration version {version} not found")

        config = self._configs[version]

        # Update fields
        if config_data.version is not None:
            # Version change requires special handling
            if config_data.version != version and config_data.version in self._configs:
                raise ValueError(f"Configuration version {config_data.version} already exists")
            
            if config_data.version != version:
                # Remove old version and create new one
                del self._configs[version]
                config.version = config_data.version
                self._configs[config.version] = config

        if config_data.model_weights is not None:
            config.model_weights = config_data.model_weights
        if config_data.thresholds is not None:
            config.thresholds = config_data.thresholds
        if config_data.feature_flags is not None:
            config.feature_flags = config_data.feature_flags
        if config_data.description is not None:
            config.description = config_data.description
        if config_data.is_active is not None:
            # If activating, deactivate others
            if config_data.is_active:
                for other_config in self._configs.values():
                    if other_config.version != config.version:
                        other_config.is_active = False
            config.is_active = config_data.is_active

        config.updated_at = datetime.utcnow()
        self._save_configs()

        logger.info(f"Updated configuration version {config.version}")
        return config

    def delete_config(self, version: str) -> bool:
        """Delete a configuration.

        Args:
            version: Configuration version

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete the only configuration
        """
        if version not in self._configs:
            return False

        if len(self._configs) == 1:
            raise ValueError("Cannot delete the only configuration")

        del self._configs[version]
        self._save_configs()

        logger.info(f"Deleted configuration version {version}")
        return True

    def activate_config(self, version: str) -> ProbabilityConfigDTO:
        """Activate a configuration (deactivates others).

        Args:
            version: Configuration version to activate

        Returns:
            Activated configuration DTO

        Raises:
            ValueError: If version doesn't exist
        """
        if version not in self._configs:
            raise ValueError(f"Configuration version {version} not found")

        # Deactivate all
        for config in self._configs.values():
            config.is_active = False

        # Activate requested
        config = self._configs[version]
        config.is_active = True
        config.updated_at = datetime.utcnow()
        self._save_configs()

        logger.info(f"Activated configuration version {version}")
        return config

    def validate_config(self, config: ProbabilityConfigDTO) -> List[str]:
        """Validate a configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate weights sum (if applicable)
        weights = config.model_weights
        total_weight = (
            weights.goals_for_weight +
            weights.goals_against_weight
        )
        if total_weight > 1.0:
            errors.append(f"Total weight exceeds 1.0: {total_weight}")

        # Validate thresholds
        thresholds = config.thresholds
        if thresholds.min_goals_for_avg >= thresholds.max_goals_for_avg:
            errors.append("min_goals_for_avg must be less than max_goals_for_avg")
        if thresholds.min_goals_against_avg >= thresholds.max_goals_against_avg:
            errors.append("min_goals_against_avg must be less than max_goals_against_avg")
        if thresholds.min_league_avg_goals >= thresholds.max_league_avg_goals:
            errors.append("min_league_avg_goals must be less than max_league_avg_goals")
        if thresholds.min_home_advantage >= thresholds.max_home_advantage:
            errors.append("min_home_advantage must be less than max_home_advantage")

        return errors


# Global configuration service instance
config_service = ProbabilityConfigService()

