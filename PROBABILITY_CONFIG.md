# Probability Model Configuration Service

## Overview

A comprehensive configuration service for managing probability model parameters, including model weights, thresholds, feature flags, and version control.

## Features

### 1. Model Weights
- Home advantage factor
- Form weight (recent form)
- Head-to-head weight
- League position weight
- Goals for/against weights

### 2. Thresholds
- Goals for/against min/max
- League average goals range
- Home advantage range
- Probability confidence threshold

### 3. Feature Flags
- Enable/disable form factor
- Enable/disable head-to-head
- Enable/disable league position factor
- Weather adjustments
- Injury adjustments
- Motivation factor
- Weighted averages
- Advanced xG

### 4. Version Control
- Multiple configuration versions
- Active configuration tracking
- Version history
- Easy rollback

## JSON Configuration Format

Configurations are stored in `config/probability_models.json`:

```json
{
  "metadata": {
    "last_updated": "2024-01-01T00:00:00",
    "total_configurations": 2
  },
  "configurations": {
    "1.0.0": {
      "version": "1.0.0",
      "model_weights": {
        "home_advantage": 0.3,
        "form_weight": 0.2,
        "head_to_head_weight": 0.1,
        "league_position_weight": 0.1,
        "goals_for_weight": 0.3,
        "goals_against_weight": 0.3
      },
      "thresholds": {
        "min_goals_for_avg": 0.0,
        "max_goals_for_avg": 10.0,
        "min_goals_against_avg": 0.0,
        "max_goals_against_avg": 10.0,
        "min_league_avg_goals": 0.5,
        "max_league_avg_goals": 5.0,
        "min_home_advantage": 0.0,
        "max_home_advantage": 1.0,
        "probability_confidence_threshold": 0.6
      },
      "feature_flags": {
        "enable_form_factor": false,
        "enable_head_to_head": false,
        "enable_league_position": false,
        "enable_weather_adjustment": false,
        "enable_injury_adjustment": false,
        "enable_motivation_factor": false,
        "use_weighted_averages": false,
        "enable_advanced_xg": false
      },
      "description": "Default configuration",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  }
}
```

## API Endpoints

All endpoints require admin authentication via `Authorization: Bearer <token>` header.

### Get All Configurations

```bash
GET /api/v1/admin/probability-config
Authorization: Bearer <admin_token>
```

### Get Active Configuration

```bash
GET /api/v1/admin/probability-config/active
Authorization: Bearer <admin_token>
```

### Get Configuration by Version

```bash
GET /api/v1/admin/probability-config/{version}
Authorization: Bearer <admin_token>
```

### Create Configuration

```bash
POST /api/v1/admin/probability-config
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "version": "1.1.0",
  "model_weights": {
    "home_advantage": 0.35,
    "form_weight": 0.25
  },
  "description": "Updated configuration with higher home advantage",
  "is_active": false
}
```

### Update Configuration

```bash
PUT /api/v1/admin/probability-config/{version}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "model_weights": {
    "home_advantage": 0.4
  },
  "is_active": true
}
```

### Delete Configuration

```bash
DELETE /api/v1/admin/probability-config/{version}
Authorization: Bearer <admin_token>
```

### Activate Configuration

```bash
POST /api/v1/admin/probability-config/{version}/activate
Authorization: Bearer <admin_token>
```

### Validate Configuration

```bash
POST /api/v1/admin/probability-config/validate
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "version": "1.2.0",
  "model_weights": {...},
  "thresholds": {...}
}
```

## Validation Rules

1. **Weights**: Must be between 0.0 and 1.0
2. **Thresholds**: Min values must be less than max values
3. **Version**: Must be unique and non-empty string
4. **Active Config**: Only one configuration can be active at a time

## Usage Examples

### Create a New Configuration

```python
from app.infrastructure.config.probability_config_service import config_service
from app.application.dto.probability_config_dto import (
    ProbabilityConfigCreateDTO,
    ModelWeightsDTO,
    ThresholdsDTO,
    FeatureFlagsDTO,
)

# Create new configuration
config_data = ProbabilityConfigCreateDTO(
    version="2.0.0",
    model_weights=ModelWeightsDTO(
        home_advantage=0.4,
        form_weight=0.3,
    ),
    feature_flags=FeatureFlagsDTO(
        enable_form_factor=True,
        enable_head_to_head=True,
    ),
    description="Enhanced configuration with form and H2H",
    is_active=False,
)

config = config_service.create_config(config_data)
```

### Get Active Configuration

```python
from app.infrastructure.config.probability_config_service import config_service

# Get active configuration
active_config = config_service.get_config()

if active_config:
    print(f"Active version: {active_config.version}")
    print(f"Home advantage: {active_config.model_weights.home_advantage}")
    print(f"Form enabled: {active_config.feature_flags.enable_form_factor}")
```

### Use Configuration in Probability Service

```python
from app.infrastructure.config.probability_config_service import config_service
from app.application.services.probability_service import ProbabilityService

# Get active configuration
config = config_service.get_config()

# Use configuration values
xg, probs = ProbabilityService.calculate_probabilities_from_stats(
    home_goals_for_avg=1.8,
    home_goals_against_avg=1.2,
    away_goals_for_avg=1.5,
    away_goals_against_avg=1.3,
    league_avg_goals=2.5,
    home_advantage=config.model_weights.home_advantage,
)
```

## Authentication

### Development Mode
If `ADMIN_TOKEN` is not set in environment variables, all endpoints are accessible (development mode).

### Production Mode
Set `ADMIN_TOKEN` in `.env`:

```env
ADMIN_TOKEN=your-secure-admin-token-here
```

Then use in requests:

```bash
curl -H "Authorization: Bearer your-secure-admin-token-here" \
     http://localhost:8000/api/v1/admin/probability-config
```

## Configuration File Location

Default location: `backend/config/probability_models.json`

Can be customized by passing `config_file` parameter to `ProbabilityConfigService`.

## Error Handling

- **404**: Configuration version not found
- **409**: Version already exists
- **422**: Validation errors
- **401/403**: Authentication/authorization errors
- **500**: Server errors

## Best Practices

1. **Version Naming**: Use semantic versioning (e.g., "1.0.0", "1.1.0", "2.0.0")
2. **Testing**: Validate configurations before activating
3. **Backup**: Keep backups of configuration file
4. **Documentation**: Add descriptions to configurations
5. **Gradual Rollout**: Test new configurations before activating

## Future Enhancements

- [ ] Configuration templates
- [ ] A/B testing support
- [ ] Configuration comparison
- [ ] Rollback functionality
- [ ] Configuration history/audit log
- [ ] Environment-specific configurations

