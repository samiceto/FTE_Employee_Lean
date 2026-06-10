#!/usr/bin/env python3
"""
Test Odoo Integration
Tests the complete Odoo → MCP Server → Skills pipeline
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from skills import get_registry, SkillInput


def test_odoo_connection():
    """Test 1: Check Odoo connection"""
    print("\n=== Test 1: Odoo Connection ===")

    try:
        registry = get_registry()
        registry.auto_discover(Path("src/skills"))

        # Get OdooConnector skill
        odoo_skill = registry.get_skill(
            "odoo_connector",
            vault_path="./ai_employee_vault",
            odoo_url="http://localhost:8069",
            odoo_db="FTE",
            odoo_user=os.getenv("ODOO_USER", "admin"),
            odoo_password=os.getenv("ODOO_PASSWORD", "")
        )

        # Test connection
        if odoo_skill.test_connection():
            print("✅ Odoo connection successful!")
            return True
        else:
            print("❌ Odoo connection failed")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_financial_summary():
    """Test 2: Get financial summary"""
    print("\n=== Test 2: Financial Summary ===")

    try:
        registry = get_registry()
        odoo_skill = registry.get_skill(
            "odoo_connector",
            vault_path="./ai_employee_vault"
        )

        # Get monthly summary
        result = odoo_skill.execute(SkillInput(data={
            "action": "get_financial_summary",
            "period": "month"
        }))

        if result.success:
            data = result.result
            print(f"✅ Financial Summary:")
            print(f"   Revenue: ${data['revenue']:.2f}")
            print(f"   Expenses: ${data['expenses']:.2f}")
            print(f"   Profit: ${data['profit']:.2f}")
            print(f"   Margin: {data['profit_margin']}%")
            return True
        else:
            print(f"❌ Failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_invoice_generation():
    """Test 3: Generate invoice with AI"""
    print("\n=== Test 3: AI Invoice Generation ===")

    try:
        registry = get_registry()

        # Use InvoiceGenerator to parse natural language
        invoice_gen = registry.get_skill(
            "invoice_generator",
            vault_path="./ai_employee_vault"
        )

        result = invoice_gen.execute(SkillInput(data={
            "description": "Invoice ABC Corp for 10 hours of consulting at $150/hour"
        }))

        if result.success:
            invoice_data = result.result
            print(f"✅ Generated invoice data:")
            print(f"   Customer: {invoice_data['partner_name']}")
            for line in invoice_data['invoice_lines']:
                print(f"   - {line['product']}: {line['quantity']} × ${line['price']}")
            return True
        else:
            print(f"❌ Failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_expense_tracking():
    """Test 4: Track expense with AI"""
    print("\n=== Test 4: AI Expense Tracking ===")

    try:
        registry = get_registry()

        expense_tracker = registry.get_skill(
            "expense_tracker",
            vault_path="./ai_employee_vault"
        )

        result = expense_tracker.execute(SkillInput(data={
            "description": "Bought office supplies from Staples for $150.50"
        }))

        if result.success:
            expense_data = result.result
            print(f"✅ Categorized expense:")
            print(f"   Description: {expense_data['description']}")
            print(f"   Amount: ${expense_data['amount']}")
            print(f"   Category: {expense_data['category']}")
            print(f"   Vendor: {expense_data.get('vendor_name', 'N/A')}")
            return True
        else:
            print(f"❌ Failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_create_invoice():
    """Test 5: Actually create invoice in Odoo"""
    print("\n=== Test 5: Create Invoice in Odoo ===")

    try:
        registry = get_registry()

        odoo_skill = registry.get_skill(
            "odoo_connector",
            vault_path="./ai_employee_vault"
        )

        result = odoo_skill.execute(SkillInput(data={
            "action": "create_invoice",
            "partner_name": "Test Customer AI",
            "invoice_lines": [
                {"product": "AI Consulting", "quantity": 5, "price": 100.0}
            ]
        }))

        if result.success:
            data = result.result
            print(f"✅ Invoice created:")
            print(f"   Number: {data['invoice_number']}")
            print(f"   Amount: ${data['amount']:.2f}")
            print(f"   State: {data['state']}")
            return True
        else:
            print(f"❌ Failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("ODOO INTEGRATION TEST SUITE")
    print("=" * 60)

    tests = [
        ("Odoo Connection", test_odoo_connection),
        ("Financial Summary", test_financial_summary),
        ("AI Invoice Generation", test_invoice_generation),
        ("AI Expense Tracking", test_expense_tracking),
        ("Create Invoice", test_create_invoice)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Odoo integration is working!")
    else:
        print("\n⚠️  Some tests failed. Check Odoo configuration.")


if __name__ == "__main__":
    main()
