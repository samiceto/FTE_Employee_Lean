"""
Odoo MCP Server - JSON-RPC API Integration for Accounting
Provides tools for invoice creation, expense tracking, and financial reporting
"""
import json
import logging
import xmlrpc.client
import socket
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
from src.core.retry_handler import with_retry
from src.core.errors import NetworkTimeout, AuthenticationError
from src.logging.audit_logger import audit_logger

logger = logging.getLogger(__name__)

# Payment operations that should NEVER auto-retry
PAYMENT_OPERATIONS = {'create_invoice', 'record_expense', 'update_invoice'}


class OdooMCPServer:
    """
    MCP Server for Odoo Community Edition using XML-RPC API.

    Provides tools for:
    - Invoice creation and management
    - Expense tracking
    - Financial reporting
    - Customer/vendor management
    - Payment processing
    """

    def __init__(
        self,
        url: str = None,
        db: str = None,
        username: str = None,
        password: str = None
    ):
        """
        Initialize Odoo MCP Server.

        Args:
            url: Odoo server URL (defaults to env ODOO_URL or localhost)
            db: Database name (defaults to env ODOO_DB or "odoo")
            username: Odoo username (defaults to env ODOO_USER or "admin")
            password: Odoo password (defaults to env ODOO_PASSWORD - REQUIRED)
        """
        import os
        from dotenv import load_dotenv

        load_dotenv()

        # Use environment variables as fallback
        self.url = url or os.getenv("ODOO_URL", "http://localhost:8069")
        self.db = db or os.getenv("ODOO_DB", "odoo")
        self.username = username or os.getenv("ODOO_USER", "admin")
        self.password = password or os.getenv("ODOO_PASSWORD")

        if not self.password:
            raise ValueError(
                "Odoo password required! Set ODOO_PASSWORD environment variable or pass password parameter"
            )
        self.uid = None
        self.models = None
        self.common = None

        self._connect()

    def _connect(self) -> bool:
        """
        Connect to Odoo using XML-RPC with timeout.

        Returns:
            True if connection successful

        Raises:
            AuthenticationError: If authentication fails
            NetworkTimeout: If connection times out
        """
        # Set socket timeout for connection
        old_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(10)  # 10 second timeout

        try:
            # Common endpoint for authentication
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')

            # Authenticate
            self.uid = self.common.authenticate(
                self.db, self.username, self.password, {}
            )

            if not self.uid:
                raise AuthenticationError("Odoo authentication failed")

            # Models endpoint for operations
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            logger.info(f"Connected to Odoo at {self.url} as user {self.username}")
            return True

        except socket.timeout:
            raise NetworkTimeout(f"Odoo connection timeout to {self.url}")
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Failed to connect to Odoo: {e}")
            raise
        finally:
            socket.setdefaulttimeout(old_timeout)

    def _is_payment_operation(self, model: str, method: str) -> bool:
        """
        Check if operation involves financial transactions.

        CRITICAL: Payment operations should NEVER auto-retry to prevent
        double-charging or duplicate transactions.

        Args:
            model: Odoo model name
            method: Method name

        Returns:
            True if this is a payment-related operation
        """
        # Check if creating/updating invoices or expenses
        if model == 'account.move' and method in ['create', 'write']:
            return True
        return False

    def _execute_once(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute operation once without retry.

        Args:
            model: Odoo model name
            method: Method name
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result

        Raises:
            NetworkTimeout: If operation times out
        """
        try:
            args_list = list(args)
            logger.debug(f"_execute_once: model={model}, method={method}")
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args_list, kwargs
            )
        except socket.timeout:
            raise NetworkTimeout(f"Odoo operation {model}.{method} timed out")

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute an Odoo model method with conditional retry and audit logging.

        Payment operations (invoice/expense creation) NEVER auto-retry.
        Safe read operations can retry on transient failures.

        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method name (e.g., 'create', 'search', 'read')
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Method result
        """
        # Log MCP call
        tool_name = f"{model}.{method}"
        audit_logger.log_mcp_call(
            server='odoo',
            tool=tool_name,
            arguments={'args': args[:3] if len(args) > 3 else args, 'kwargs': kwargs}  # Truncate for privacy
        )

        start_time = time.time()

        try:
            # CRITICAL: Never auto-retry payment operations
            if self._is_payment_operation(model, method):
                logger.warning(f"Payment operation {model}.{method} - no auto-retry")
                result = self._execute_once(model, method, *args, **kwargs)
            else:
                # Safe operations can retry
                @with_retry(max_attempts=3)
                def _execute_with_retry():
                    return self._execute_once(model, method, *args, **kwargs)

                result = _execute_with_retry()

            # Log success
            duration_ms = (time.time() - start_time) * 1000
            audit_logger.log_mcp_success(
                server='odoo',
                tool=tool_name,
                duration_ms=duration_ms
            )

            return result

        except Exception as e:
            # Log failure
            duration_ms = (time.time() - start_time) * 1000
            audit_logger.log_mcp_failure(
                server='odoo',
                tool=tool_name,
                error=str(e),
                duration_ms=duration_ms
            )
            raise

    # ==================== TOOL: create_invoice ====================
    def create_invoice(
        self,
        partner_name: str,
        invoice_lines: List[Dict[str, Any]],
        invoice_type: str = "out_invoice"
    ) -> Dict[str, Any]:
        """
        Create a customer invoice or vendor bill in Odoo.

        Args:
            partner_name: Customer or vendor name
            invoice_lines: List of invoice lines with 'product', 'quantity', 'price'
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor bill)

        Returns:
            Invoice details including ID and number

        Example:
            create_invoice(
                partner_name="ABC Corp",
                invoice_lines=[
                    {"product": "Consulting Services", "quantity": 10, "price": 150.0},
                    {"product": "Development", "quantity": 20, "price": 200.0}
                ]
            )
        """
        try:
            # Find or create partner
            partner_id = self._get_or_create_partner(partner_name)

            # Prepare invoice lines
            line_ids = []
            for line in invoice_lines:
                # Find or create product
                product_id = self._get_or_create_product(line['product'])

                line_ids.append((0, 0, {
                    'product_id': product_id,
                    'quantity': line['quantity'],
                    'price_unit': line['price'],
                    'name': line['product']
                }))

            # Create invoice
            invoice_id = self._execute('account.move', 'create', {
                'move_type': invoice_type,
                'partner_id': partner_id,
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_line_ids': line_ids
            })

            # Read invoice details
            invoice = self._execute('account.move', 'read', invoice_id,
                fields=['name', 'invoice_date', 'amount_total', 'state'])[0]

            logger.info(f"Created invoice {invoice['name']} for {partner_name}")

            return {
                'success': True,
                'invoice_id': invoice_id,
                'invoice_number': invoice['name'],
                'amount': invoice['amount_total'],
                'state': invoice['state'],
                'message': f"Invoice {invoice['name']} created successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== TOOL: record_expense ====================
    def record_expense(
        self,
        description: str,
        amount: float,
        category: str = "Office Expenses",
        vendor_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a business expense in Odoo.

        Args:
            description: Expense description
            amount: Expense amount
            category: Expense category (account name)
            vendor_name: Vendor name (optional)

        Returns:
            Expense record details

        Example:
            record_expense(
                description="Office supplies",
                amount=150.50,
                category="Office Expenses",
                vendor_name="Staples"
            )
        """
        try:
            # Find expense account
            expense_account = self._execute('account.account', 'search_read',
                [('name', 'ilike', category)],
                fields=['id'], limit=1)

            if not expense_account:
                return {
                    'success': False,
                    'error': f'Expense account "{category}" not found'
                }

            account_id = expense_account[0]['id']

            # Get or create vendor
            partner_id = None
            if vendor_name:
                partner_id = self._get_or_create_partner(vendor_name, is_vendor=True)

            # Create vendor bill (expense)
            bill_data = {
                'move_type': 'in_invoice',
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'invoice_line_ids': [(0, 0, {
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount,
                    'account_id': account_id
                })]
            }

            if partner_id:
                bill_data['partner_id'] = partner_id

            bill_id = self._execute('account.move', 'create', bill_data)

            # Read bill details
            bill = self._execute('account.move', 'read', bill_id,
                fields=['name', 'amount_total', 'state'])[0]

            logger.info(f"Recorded expense: {description} - ${amount}")

            return {
                'success': True,
                'expense_id': bill_id,
                'expense_number': bill['name'],
                'amount': bill['amount_total'],
                'state': bill['state'],
                'message': f"Expense {bill['name']} recorded successfully"
            }

        except Exception as e:
            logger.error(f"Failed to record expense: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== TOOL: get_accounts_receivable ====================
    def get_accounts_receivable(self) -> Dict[str, Any]:
        """
        Get outstanding customer invoices (accounts receivable).

        Returns:
            List of unpaid invoices with details

        Example:
            get_accounts_receivable()
        """
        try:
            # Search for posted, unpaid customer invoices
            unpaid_invoices = self._execute('account.move', 'search_read',
                [('move_type', '=', 'out_invoice'),
                 ('state', '=', 'posted'),
                 ('payment_state', 'in', ['not_paid', 'partial'])],
                fields=['name', 'partner_id', 'invoice_date', 'invoice_date_due',
                       'amount_total', 'amount_residual', 'payment_state'])

            total_due = sum(inv['amount_residual'] for inv in unpaid_invoices)

            logger.info(f"Found {len(unpaid_invoices)} unpaid invoices, total: ${total_due}")

            return {
                'success': True,
                'total_due': total_due,
                'invoice_count': len(unpaid_invoices),
                'invoices': [
                    {
                        'invoice_number': inv['name'],
                        'customer': inv['partner_id'][1] if inv['partner_id'] else 'Unknown',
                        'date': inv['invoice_date'],
                        'due_date': inv['invoice_date_due'],
                        'total': inv['amount_total'],
                        'due': inv['amount_residual'],
                        'status': inv['payment_state']
                    }
                    for inv in unpaid_invoices
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get accounts receivable: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== TOOL: get_financial_summary ====================
    def get_financial_summary(self, period: str = "month") -> Dict[str, Any]:
        """
        Get financial summary for a period.

        Args:
            period: 'month', 'quarter', or 'year'

        Returns:
            Financial summary with revenue, expenses, profit

        Example:
            get_financial_summary(period="month")
        """
        try:
            # Calculate date range
            today = datetime.now()
            if period == "month":
                start_date = today.replace(day=1).strftime('%Y-%m-%d')
            elif period == "quarter":
                quarter_start = ((today.month - 1) // 3) * 3 + 1
                start_date = today.replace(month=quarter_start, day=1).strftime('%Y-%m-%d')
            else:  # year
                start_date = today.replace(month=1, day=1).strftime('%Y-%m-%d')

            end_date = today.strftime('%Y-%m-%d')

            # Get revenue (customer invoices)
            revenue_invoices = self._execute('account.move', 'search_read',
                [('move_type', '=', 'out_invoice'),
                 ('state', '=', 'posted'),
                 ('invoice_date', '>=', start_date),
                 ('invoice_date', '<=', end_date)],
                fields=['amount_total'])

            total_revenue = sum(inv['amount_total'] for inv in revenue_invoices)

            # Get expenses (vendor bills)
            expense_bills = self._execute('account.move', 'search_read',
                [('move_type', '=', 'in_invoice'),
                  ('state', '=', 'posted'),
                  ('invoice_date', '>=', start_date),
                  ('invoice_date', '<=', end_date)],
                fields=['amount_total'])

            total_expenses = sum(bill['amount_total'] for bill in expense_bills)

            profit = total_revenue - total_expenses
            margin = (profit / total_revenue * 100) if total_revenue > 0 else 0

            logger.info(f"Financial summary for {period}: Revenue=${total_revenue}, Expenses=${total_expenses}, Profit=${profit}")

            return {
                'success': True,
                'period': period,
                'start_date': start_date,
                'end_date': end_date,
                'revenue': total_revenue,
                'expenses': total_expenses,
                'profit': profit,
                'profit_margin': round(margin, 2),
                'invoice_count': len(revenue_invoices),
                'expense_count': len(expense_bills)
            }

        except Exception as e:
            logger.error(f"Failed to get financial summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== Helper Methods ====================
    def _get_or_create_partner(self, name: str, is_vendor: bool = False) -> int:
        """Get existing partner or create new one"""
        partners = self._execute('res.partner', 'search', [('name', '=', name)])

        if partners:
            return partners[0]

        # Create new partner
        partner_data = {
            'name': name,
            'customer_rank': 1 if not is_vendor else 0,
            'supplier_rank': 1 if is_vendor else 0
        }

        return self._execute('res.partner', 'create', partner_data)

    def _get_or_create_product(self, name: str) -> int:
        """Get existing product or create new one"""
        products = self._execute('product.product', 'search', [('name', '=', name)])

        if products:
            return products[0]

        # Create new product
        return self._execute('product.product', 'create', {
            'name': name,
            'type': 'service',
            'list_price': 0.0
        })


# ==================== MCP Tool Definitions ====================
# These would be registered with the MCP framework

MCP_TOOLS = [
    {
        "name": "odoo_create_invoice",
        "description": "Create a customer invoice or vendor bill in Odoo accounting system",
        "parameters": {
            "type": "object",
            "properties": {
                "partner_name": {
                    "type": "string",
                    "description": "Customer or vendor name"
                },
                "invoice_lines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product": {"type": "string"},
                            "quantity": {"type": "number"},
                            "price": {"type": "number"}
                        }
                    },
                    "description": "Invoice line items"
                },
                "invoice_type": {
                    "type": "string",
                    "enum": ["out_invoice", "in_invoice"],
                    "description": "Invoice type: out_invoice for customer, in_invoice for vendor"
                }
            },
            "required": ["partner_name", "invoice_lines"]
        }
    },
    {
        "name": "odoo_record_expense",
        "description": "Record a business expense in Odoo",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Expense description"},
                "amount": {"type": "number", "description": "Expense amount"},
                "category": {"type": "string", "description": "Expense category"},
                "vendor_name": {"type": "string", "description": "Vendor name (optional)"}
            },
            "required": ["description", "amount"]
        }
    },
    {
        "name": "odoo_get_accounts_receivable",
        "description": "Get outstanding customer invoices (money owed to you)",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "odoo_get_financial_summary",
        "description": "Get financial summary (revenue, expenses, profit) for a period",
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["month", "quarter", "year"],
                    "description": "Time period for summary"
                }
            }
        }
    }
]


if __name__ == "__main__":
    # Test the Odoo connection
    logging.basicConfig(level=logging.INFO)

    try:
        odoo = OdooMCPServer()
        print("✅ Connected to Odoo successfully!")

        # Test creating an invoice
        result = odoo.create_invoice(
            partner_name="Test Customer",
            invoice_lines=[
                {"product": "Consulting", "quantity": 5, "price": 100.0}
            ]
        )
        print(f"\n Invoice creation: {result}")

        # Test financial summary
        summary = odoo.get_financial_summary("month")
        print(f"\n Financial summary: {summary}")

    except Exception as e:
        print(f"❌ Error: {e}")
