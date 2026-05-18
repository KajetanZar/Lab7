from src.models import Bill, Parameters, TenantSettlement, ApartmentSettlement, Transfer
from src.manager import Manager


def test_settlement_due_between_tanants_and_apartment():
    manager = Manager(Parameters())

    settlement: ApartmentSettlement = manager.get_settlement('apart-polanka', 2025, 1)
    
    tenants_settlements: list[TenantSettlement] = manager.create_tenants_settlements(settlement)
    assert len(tenants_settlements) == 3

    total_due = sum([tenant_settlement.total_due_pln for tenant_settlement in tenants_settlements])
    assert total_due == settlement.total_due_pln

def test_debtors_calculation():
    manager = Manager(Parameters())

    debtors = manager.get_debtors('apart-polanka', 2025, 1)
    assert len(debtors) == 0

    debtors = manager.get_debtors('apart-polanka', 2025, 2)
    assert len(debtors) == 3


def test_tax_calculation():
    manager = Manager(Parameters())
    
    tax = manager.calculate_tax(2025, 1, 0.085)
    assert tax == 638 # 0.085 * 7500.0

    tax = manager.calculate_tax(2025, 2, 0.085)
    assert tax == 0

def test_deposits_calculation():
    manager = Manager(Parameters())
    
    deposit_balance = manager.check_deposits()
    assert deposit_balance == -8700.0 # no deposit in transfers

    manager.transfers.append(Transfer(
        tenant='tenant-1',
        date='2025-01-01',
        settlement_year=None,
        settlement_month=None,
        amount_pln=1000.0,
        type='deposit'
    ))

    deposit_balance = manager.check_deposits()
    assert deposit_balance == -7700.0 # 1000.0 deposit in transfers

def test_annual_balance_calculation():
    manager = Manager(Parameters())
    
    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 6490.0 # 7500.0 in transfers minus 910.0 in bills

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-02-15',
        settlement_year=2025,
        settlement_month=5,
        amount_pln=500.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-02-15',
        settlement_year=2025,
        settlement_month=5,
        amount_pln=4500.0,
        type='renovation'
    ))

    annual_balance = manager.get_annual_balance(2025)
    assert annual_balance == 1490.0 # 7500.0 in transfers minus 910.0 in bills minus new bills 500.0 and 4500.0

def test_apartment_has_any_bills():
    manager = Manager(Parameters())
    
    has_bills = manager.has_any_bills('apart-polanka', 2025, 1)
    assert has_bills == True

    has_bills = manager.has_any_bills('apart-polanka', 2025, 3)
    assert has_bills == False

def test_validate_transfer_to_nonexistent_tenant():
    manager = Manager(Parameters())
    transfer = Transfer(
        tenant='nonexistent-tenant',
        date='2025-01-15',
        settlement_year=2025,
        settlement_month=1,
        amount_pln=1500.00,
        type='payment'
    )
    errors = manager.check_transfer_validity(transfer)
    assert len(errors) > 0
    assert any('najemca' in error.lower() or 'tenant' in error.lower() for error in errors)

def test_validate_transfer_outside_tenant_agreement_dates():
    manager = Manager(Parameters())
    transfer = Transfer(
        tenant='tenant-1',
        date='2026-06-15',
        settlement_year=2026,
        settlement_month=6,
        amount_pln=1500.00,
        type='payment'
    )
    errors = manager.check_transfer_validity(transfer)
    assert len(errors) > 0
    assert any('umowa' in error.lower() or 'agreement' in error.lower() or 'okres' in error.lower() for error in errors)

def test_validate_transfer_within_tenant_agreement_dates():
    manager = Manager(Parameters())
    transfer = Transfer(
        tenant='tenant-1',
        date='2025-06-15',
        settlement_year=2025,
        settlement_month=6,
        amount_pln=1500.00,
        type='payment'
    )
    errors = manager.check_transfer_validity(transfer)
    assert not any('umowa' in error.lower() or 'agreement' in error.lower() for error in errors)
