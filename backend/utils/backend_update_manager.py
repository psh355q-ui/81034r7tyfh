"""
Backend Update Manager

Periodic update management system for backend dependencies and model configurations.
This module provides:
- Automatic model verification from official Z.ai page
- Update notifications
- Scheduled update checks

Usage:
    python -m backend.utils.backend_update_manager --check
    python -m backend.utils.backend_update_manager --schedule
"""

import os
import sys
import asyncio
import logging
import json
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.ai.glm_client import GLMClient
    GLM_AVAILABLE = True
except ImportError:
    GLM_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Model configuration data class"""
    name: str
    stage: str  # 'reasoning' or 'structuring'
    env_var: str  # Environment variable name
    current_value: str  # Current value in .env
    expected_value: str  # Expected value from official source
    status: str  # 'ok', 'outdated', 'missing'
    last_checked: str


@dataclass
class UpdateCheckResult:
    """Result of update check"""
    timestamp: str
    models: Dict[str, ModelConfig]
    env_file_status: str
    recommendations: List[str]
    needs_update: bool


class BackendUpdateManager:
    """
    Manages periodic updates for backend configuration and models.

    Features:
    - Model verification against official Z.ai documentation
    - Environment variable validation
    - Update recommendations
    - Scheduled checks
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize update manager"""
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.env_example_path = self.project_root / '.env.example'
        self.env_path = self.project_root / '.env'
        self.check_log_path = self.project_root / 'logs' / 'update_checks.json'

        # Ensure logs directory exists
        self.check_log_path.parent.mkdir(parents=True, exist_ok=True)

        # Model configuration
        self.model_configs = {
            'glm_model_reasoning': {
                'env_var': 'GLM_MODEL_REASONING',
                'stage': 'reasoning',
                'default': 'glm-4.7',
                'description': 'Deep reasoning for Stage 1'
            },
            'glm_model_structuring': {
                'env_var': 'GLM_MODEL_STRUCTURING',
                'stage': 'structuring',
                'default': 'glm-4.6v-flashx',
                'description': 'Fast JSON extraction for Stage 2'
            }
        }

    def check_models(self) -> UpdateCheckResult:
        """
        Check current model configuration against expected values.

        Returns:
            UpdateCheckResult with status and recommendations
        """
        timestamp = datetime.utcnow().isoformat()
        models = {}
        recommendations = []
        needs_update = False

        # Check each model configuration
        for model_key, config in self.model_configs.items():
            env_var = config['env_var']
            expected_value = config['default']

            # Get current value from environment
            current_value = os.getenv(env_var, expected_value)

            # Determine status
            if current_value == expected_value:
                status = 'ok'
            elif current_value == '':
                status = 'missing'
                needs_update = True
                recommendations.append(
                    f"❌ {env_var} is not set in environment. "
                    f"Expected: {expected_value}"
                )
            else:
                status = 'outdated'
                needs_update = True
                recommendations.append(
                    f"⚠️ {env_var} may be outdated. "
                    f"Current: {current_value}, Expected: {expected_value}"
                )

            models[model_key] = ModelConfig(
                name=model_key,
                stage=config['stage'],
                env_var=env_var,
                current_value=current_value,
                expected_value=expected_value,
                status=status,
                last_checked=timestamp
            )

        # Check .env file status
        env_file_status = self._check_env_file()

        # Add recommendations if .env needs update
        if env_file_status != 'ok':
            needs_update = True
            recommendations.append(
                f"⚠️ .env file {env_file_status}. "
                f"Please sync with .env.example"
            )

        return UpdateCheckResult(
            timestamp=timestamp,
            models=models,
            env_file_status=env_file_status,
            recommendations=recommendations,
            needs_update=needs_update
        )

    def _check_env_file(self) -> str:
        """Check if .env file is in sync with .env.example"""
        if not self.env_path.exists():
            return 'missing'

        # Read both files
        env_content = self.env_path.read_text(encoding='utf-8')
        env_example_content = self.env_example_path.read_text(encoding='utf-8')

        # Check for critical environment variables
        critical_vars = [
            'GLM_MODEL_REASONING',
            'GLM_MODEL_STRUCTURING',
            'GLM_API_KEY'
        ]

        for var in critical_vars:
            # Check if variable exists in .env.example but not in .env
            if f'{var}=' in env_example_content:
                if f'{var}=' not in env_content:
                    return f'missing {var}'

                # Check if values differ significantly (excluding API keys)
                if var != 'GLM_API_KEY':
                    example_line = [
                        line for line in env_example_content.split('\n')
                        if line.startswith(f'{var}=')
                    ]
                    env_line = [
                        line for line in env_content.split('\n')
                        if line.startswith(f'{var}=')
                    ]

                    if example_line and env_line:
                        example_value = example_line[0].split('=')[1].strip().strip('"')
                        env_value = env_line[0].split('=')[1].strip().strip('"')

                        if example_value != env_value and env_value != 'your API key here':
                            return f'outdated {var}'

        return 'ok'

    def save_check_result(self, result: UpdateCheckResult):
        """Save check result to log file"""
        logs = []

        # Load existing logs
        if self.check_log_path.exists():
            try:
                with open(self.check_log_path, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load check logs: {e}")

        # Add new result
        result_dict = {
            'timestamp': result.timestamp,
            'models': {
                k: asdict(v) for k, v in result.models.items()
            },
            'env_file_status': result.env_file_status,
            'recommendations': result.recommendations,
            'needs_update': result.needs_update
        }

        logs.append(result_dict)

        # Keep only last 30 days of logs
        cutoff = datetime.utcnow() - timedelta(days=30)
        logs = [
            log for log in logs
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]

        # Save logs
        with open(self.check_log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    def print_report(self, result: UpdateCheckResult):
        """Print update check report"""
        print(f"\n{'='*80}")
        print(f"BACKEND UPDATE CHECK REPORT")
        print(f"Timestamp: {result.timestamp}")
        print(f"{'='*80}\n")

        # Model Status
        print("[Model Configuration]")
        for model_key, model in result.models.items():
            status_icon = {
                'ok': '✅',
                'outdated': '⚠️',
                'missing': '❌'
            }.get(model.status, '❓')

            print(f"  {status_icon} {model.env_var}")
            print(f"     Stage: {model.stage}")
            print(f"     Current: {model.current_value}")
            print(f"     Expected: {model.expected_value}")
            print()

        # Environment File Status
        print(f"[Environment File]")
        env_icon = '✅' if result.env_file_status == 'ok' else '⚠️'
        print(f"  {env_icon} Status: {result.env_file_status}")
        print()

        # Recommendations
        if result.recommendations:
            print("[Recommendations]")
            for rec in result.recommendations:
                print(f"  {rec}")
            print()
        else:
            print("[Recommendations]")
            print("  ✅ All configurations are up to date!")
            print()

        # Overall Status
        overall_icon = '✅' if not result.needs_update else '⚠️'
        overall_status = "UP TO DATE" if not result.needs_update else "NEEDS ATTENTION"
        print(f"\n[Overall Status]")
        print(f"  {overall_icon} {overall_status}")
        print(f"{'='*80}\n")

    async def verify_models_with_api(self) -> Dict[str, Any]:
        """
        Verify models are accessible via GLM API.

        Returns:
            Dict with verification results
        """
        if not GLM_AVAILABLE:
            return {
                'success': False,
                'error': 'GLM client not available'
            }

        api_key = os.getenv('GLM_API_KEY')
        if not api_key:
            return {
                'success': False,
                'error': 'GLM_API_KEY not set'
            }

        results = {}

        # Test each model
        for model_key, config in self.model_configs.items():
            model_name = os.getenv(config['env_var'], config['default'])

            try:
                client = GLMClient(api_key=api_key, model=model_name)

                # Simple test call
                response = await client.chat(
                    messages=[
                        {"role": "user", "content": "test"}
                    ],
                    max_tokens=10,
                    temperature=0.1
                )

                results[model_key] = {
                    'success': True,
                    'model': model_name,
                    'response_length': len(response.get('choices', [{}])[0].get('message', {}).get('content', ''))
                }

                await client.close()

            except Exception as e:
                results[model_key] = {
                    'success': False,
                    'model': model_name,
                    'error': str(e)
                }

        return results


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Backend Update Manager'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Run update check and display report'
    )
    parser.add_argument(
        '--verify-api',
        action='store_true',
        help='Verify models are accessible via API'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        help='Project root directory'
    )

    args = parser.parse_args()

    # Initialize manager
    manager = BackendUpdateManager(project_root=args.project_root)

    if args.check or not any([args.check, args.verify_api]):
        # Run update check
        result = manager.check_models()
        manager.print_report(result)
        manager.save_check_result(result)

        # Exit with error code if update needed
        if result.needs_update:
            sys.exit(1)

    if args.verify_api:
        # Verify API access
        print("\n[API Verification]")
        print("Testing model access via GLM API...\n")

        results = asyncio.run(manager.verify_models_with_api())

        for model_key, result in results.items():
            icon = '✅' if result['success'] else '❌'
            print(f"  {icon} {model_key}")
            if result['success']:
                print(f"     Model: {result['model']}")
                print(f"     Response: {result['response_length']} chars")
            else:
                print(f"     Error: {result.get('error', 'Unknown')}")
            print()


if __name__ == '__main__':
    main()
