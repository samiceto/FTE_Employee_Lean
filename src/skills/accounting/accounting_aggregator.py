"""
AccountingAggregator Skill - Parse financial data from Accounting/Current_Month.md and Business_Goals.md
"""
import logging
import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from skills.base_skill import BaseSkill, SkillInput, SkillOutput

logger = logging.getLogger(__name__)


class AccountingAggregator(BaseSkill):
    """
    Parse financial data from markdown accounting files.

    Extracts transactions, calculates totals, parses subscriptions,
    and tracks progress against revenue targets.

    Does NOT use LLM - Pure Python markdown parsing.
    """

    SKILL_NAME = "accounting_aggregator"
    REQUIRES_LLM = False
    DESCRIPTION = "Aggregate financial data from accounting markdown files"

    def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Parse and aggregate financial data.

        Args:
            input_data: SkillInput with data containing:
                - start_date: ISO format date string (required)
                - end_date: ISO format date string (required)
                - month_file: Path to Current_Month.md (optional, default: "Accounting/Current_Month.md")

        Returns:
            SkillOutput with financial aggregations

        Example:
            SkillInput(data={
                "start_date": "2026-01-15",
                "end_date": "2026-01-21"
            })
        """
        # Validate input
        error = self.validate_input(input_data, ["start_date", "end_date"])
        if error:
            return SkillOutput(result=None, success=False, error_message=error)

        try:
            start_date = datetime.fromisoformat(input_data.data["start_date"])
            end_date = datetime.fromisoformat(input_data.data["end_date"])

            # Get file paths
            month_file = input_data.data.get("month_file", "Accounting/Current_Month.md")
            month_path = Path(self.vault_path) / month_file
            goals_path = Path(self.vault_path) / "Business_Goals.md"

            # Parse transactions
            transactions = []
            if month_path.exists():
                transactions = self._parse_transactions(month_path)
            else:
                logger.warning(f"Month file not found: {month_path}")

            # Filter transactions by date range
            weekly_transactions = [
                t for t in transactions
                if start_date.date() <= datetime.fromisoformat(t["date"]).date() <= end_date.date()
            ]

            # Calculate weekly totals
            weekly_revenue = sum(t["amount"] for t in weekly_transactions if t["amount"] > 0)
            weekly_expenses = sum(abs(t["amount"]) for t in weekly_transactions if t["amount"] < 0)
            weekly_net = weekly_revenue - weekly_expenses

            # Calculate MTD totals
            month_start = datetime(end_date.year, end_date.month, 1)
            mtd_transactions = [
                t for t in transactions
                if month_start.date() <= datetime.fromisoformat(t["date"]).date() <= end_date.date()
            ]

            mtd_revenue = sum(t["amount"] for t in mtd_transactions if t["amount"] > 0)
            mtd_expenses = sum(abs(t["amount"]) for t in mtd_transactions if t["amount"] < 0)
            mtd_net = mtd_revenue - mtd_expenses

            # Get revenue target
            revenue_target = 0.0
            if goals_path.exists():
                revenue_target = self._extract_revenue_target(goals_path)

            # Calculate progress
            target_progress = (mtd_revenue / revenue_target * 100) if revenue_target > 0 else 0.0

            # Expenses by category
            expenses_by_category = {}
            for t in weekly_transactions:
                if t["amount"] < 0:
                    category = t.get("category", "Uncategorized")
                    expenses_by_category[category] = expenses_by_category.get(category, 0) + abs(t["amount"])

            # Parse subscriptions
            subscriptions = []
            if month_path.exists():
                subscriptions = self._parse_subscriptions(month_path)

            logger.info(f"Aggregated financial data: Weekly revenue ${weekly_revenue:.2f}, MTD ${mtd_revenue:.2f}")

            return SkillOutput(
                result={
                    "weekly_revenue": weekly_revenue,
                    "weekly_expenses": weekly_expenses,
                    "weekly_net": weekly_net,
                    "mtd_revenue": mtd_revenue,
                    "mtd_expenses": mtd_expenses,
                    "mtd_net": mtd_net,
                    "revenue_target": revenue_target,
                    "target_progress": round(target_progress, 2),
                    "transactions": weekly_transactions,
                    "expenses_by_category": expenses_by_category,
                    "subscriptions": subscriptions
                },
                success=True,
                metadata={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_transactions": len(transactions),
                    "weekly_transactions": len(weekly_transactions)
                }
            )

        except Exception as e:
            logger.error(f"AccountingAggregator execution failed: {e}")
            return SkillOutput(
                result=None,
                success=False,
                error_message=str(e)
            )

    def _parse_transactions(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse transaction table from markdown file.

        Expected format:
        | Date | Description | Amount | Category | Status |
        |------|-------------|---------|----------|--------|
        | 2026-01-15 | Invoice | $2,500.00 | Income | Paid |

        Args:
            file_path: Path to markdown file

        Returns:
            List of transaction dictionaries
        """
        transactions = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find transaction table
            in_table = False
            header_found = False

            for line in lines:
                line = line.strip()

                # Check if this is a table line
                if not line.startswith('|'):
                    if in_table:
                        # End of table
                        break
                    continue

                # Parse table cells
                cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last

                if not cells:
                    continue

                # Check for header row
                if 'Date' in cells[0] or 'date' in cells[0].lower():
                    header_found = True
                    in_table = True
                    continue

                # Skip separator row
                if header_found and all(c.replace('-', '').strip() == '' for c in cells):
                    continue

                # Parse data row
                if in_table and header_found and len(cells) >= 3:
                    # Skip empty rows
                    if not cells[0] or cells[0] == '':
                        continue

                    try:
                        date_str = cells[0].strip()
                        description = cells[1].strip() if len(cells) > 1 else ""
                        amount_str = cells[2].strip() if len(cells) > 2 else "$0"
                        category = cells[3].strip() if len(cells) > 3 else "Uncategorized"
                        status = cells[4].strip() if len(cells) > 4 else "Pending"

                        # Parse amount
                        amount = self._parse_amount(amount_str)

                        # Parse date
                        try:
                            date_obj = datetime.fromisoformat(date_str)
                            date_iso = date_obj.isoformat()
                        except ValueError:
                            logger.warning(f"Invalid date format: {date_str}")
                            continue

                        transactions.append({
                            "date": date_iso,
                            "description": description,
                            "amount": amount,
                            "category": category,
                            "status": status
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing transaction row: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing transactions from {file_path}: {e}")

        return transactions

    def _parse_subscriptions(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse subscription table from markdown file.

        Expected format:
        | Service | Cost | Last Activity | Status |
        |---------|------|---------------|--------|
        | AWS | $125.00 | 2026-01-21 | Active |

        Args:
            file_path: Path to markdown file

        Returns:
            List of subscription dictionaries
        """
        subscriptions = []

        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')

            # Find subscription table
            in_table = False
            header_found = False

            for line in lines:
                line = line.strip()

                # Check if this is a table line
                if not line.startswith('|'):
                    if in_table:
                        # End of table
                        break
                    continue

                # Parse table cells
                cells = [cell.strip() for cell in line.split('|')[1:-1]]

                if not cells:
                    continue

                # Check for header row with "Service" or "Subscription"
                if 'Service' in cells[0] or 'service' in cells[0].lower() or 'Subscription' in cells[0]:
                    header_found = True
                    in_table = True
                    continue

                # Skip separator row
                if header_found and all(c.replace('-', '').strip() == '' for c in cells):
                    continue

                # Parse data row
                if in_table and header_found and len(cells) >= 3:
                    # Skip empty rows
                    if not cells[0] or cells[0] == '':
                        continue

                    try:
                        service = cells[0].strip()
                        cost_str = cells[1].strip() if len(cells) > 1 else "$0"
                        last_activity = cells[2].strip() if len(cells) > 2 else ""
                        status = cells[3].strip() if len(cells) > 3 else "Active"

                        # Parse cost
                        cost = self._parse_amount(cost_str)

                        subscriptions.append({
                            "service": service,
                            "cost": abs(cost),  # Ensure positive
                            "last_activity": last_activity,
                            "status": status
                        })

                    except Exception as e:
                        logger.warning(f"Error parsing subscription row: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing subscriptions from {file_path}: {e}")

        return subscriptions

    def _parse_amount(self, amount_str: str) -> float:
        """
        Parse amount from string (handles $, commas, negative).

        Args:
            amount_str: Amount string like "$1,234.56" or "-$50"

        Returns:
            Float amount (negative for expenses)
        """
        try:
            # Remove currency symbols and commas
            cleaned = amount_str.replace('$', '').replace(',', '').strip()

            # Handle parentheses (accounting format for negative)
            if cleaned.startswith('(') and cleaned.endswith(')'):
                cleaned = '-' + cleaned[1:-1]

            return float(cleaned)

        except ValueError:
            logger.warning(f"Could not parse amount: {amount_str}")
            return 0.0

    def _extract_revenue_target(self, file_path: Path) -> float:
        """
        Extract revenue target from Business_Goals.md.

        Looks for line like "- Monthly goal: $10,000"

        Args:
            file_path: Path to Business_Goals.md

        Returns:
            Revenue target as float
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Look for "Monthly goal: $X" pattern
            match = re.search(r'Monthly goal:\s*\$?([\d,]+(?:\.\d{2})?)', content, re.IGNORECASE)
            if match:
                amount_str = match.group(1)
                return self._parse_amount(amount_str)

        except Exception as e:
            logger.error(f"Error extracting revenue target: {e}")

        return 0.0
