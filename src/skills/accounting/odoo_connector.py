"""
OdooConnector Skill - Integrate with Odoo accounting system
Connects to Odoo MCP server for accounting operations
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput
from mcp_servers.odoo.odoo_mcp_server import OdooMCPServer

logger = logging.getLogger(__name__)


class OdooConnector(BaseSkill):
    """
    Connect to Odoo accounting system and perform operations.

    This skill wraps the Odoo MCP server to provide accounting
    functionality as an agent skill.

    NO Groq needed - direct Odoo API calls.
    """

    SKILL_NAME = "odoo_connector"
    REQUIRES_LLM = False
    DESCRIPTION = "Connect to Odoo accounting system for invoices, expenses, and reporting"

    def __init__(
        self,
        vault_path: str,
        odoo_url: str = None,
        odoo_db: str = None,
        odoo_user: str = None,
        odoo_password: str = None,
        **kwargs
    ):
        """
        Initialize OdooConnector.

        Args:
            vault_path: Path to vault (for logging/storage)
            odoo_url: Odoo server URL (optional, reads from env)
            odoo_db: Odoo database name (optional, reads from env)
            odoo_user: Odoo username (optional, reads from env)
            odoo_password: Odoo password (optional, reads from env ODOO_PASSWORD)
        """
        super().__init__(vault_path, **kwargs)

        # Initialize Odoo MCP Server
        # Will read from environment variables if not provided
        try:
            self.odoo = OdooMCPServer(
                url=odoo_url,
                db=odoo_db,
                username=odoo_user,
                password=odoo_password
            )
            logger.info("OdooConnector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Odoo connection: {e}")
            raise

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute an Odoo operation.

        Args:
            input_data: SkillInput with data containing:
                - action: Operation to perform (required)
                  Options: "create_invoice", "record_expense",
                           "get_receivables", "get_financial_summary"
                - Additional parameters based on action

        Returns:
            SkillOutput with operation result

        Example:
            # Create invoice
            SkillInput(data={
                "action": "create_invoice",
                "partner_name": "ABC Corp",
                "invoice_lines": [
                    {"product": "Consulting", "quantity": 10, "price": 150.0}
                ]
            })

            # Record expense
            SkillInput(data={
                "action": "record_expense",
                "description": "Office supplies",
                "amount": 250.0,
                "category": "Office Expenses"
            })

            # Get receivables
            SkillInput(data={"action": "get_receivables"})

            # Get financial summary
            SkillInput(data={"action": "get_financial_summary", "period": "month"})
        """
        # Validate input
        error = self.validate_input(input_data, ["action"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            action = input_data.data["action"]
            result = None

            if action == "create_invoice":
                result = self._create_invoice(input_data.data)
            elif action == "record_expense":
                result = self._record_expense(input_data.data)
            elif action == "get_receivables":
                result = self._get_receivables()
            elif action == "get_financial_summary":
                result = self._get_financial_summary(input_data.data)
            else:
                return SkillOutput(
                    result=None,
                    success=False,
                    error_message=f"Unknown action: {action}"
                )

            if result.get("success"):
                return SkillOutput(
                    result=result,
                    success=True,
                    metadata={"action": action}
                )
            else:
                return SkillOutput(
                    result=result,
                    success=False,
                    error_message=result.get("error", "Unknown error")
                )

        except Exception as e:
            logger.error(f"OdooConnector execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _create_invoice(self, data: dict) -> dict:
        """Create invoice using Odoo"""
        return self.odoo.create_invoice(
            partner_name=data.get("partner_name"),
            invoice_lines=data.get("invoice_lines", []),
            invoice_type=data.get("invoice_type", "out_invoice")
        )

    def _record_expense(self, data: dict) -> dict:
        """Record expense using Odoo"""
        return self.odoo.record_expense(
            description=data.get("description"),
            amount=data.get("amount"),
            category=data.get("category", "Office Expenses"),
            vendor_name=data.get("vendor_name")
        )

    def _get_receivables(self) -> dict:
        """Get accounts receivable"""
        return self.odoo.get_accounts_receivable()

    def _get_financial_summary(self, data: dict) -> dict:
        """Get financial summary"""
        return self.odoo.get_financial_summary(
            period=data.get("period", "month")
        )

    def test_connection(self) -> bool:
        """
        Test if Odoo connection is working.

        Returns:
            True if connection successful
        """
        try:
            # Try to get financial summary as connection test
            result = self.odoo.get_financial_summary("month")
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
