import json

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


def test_check_tenant_blacklist_returns_reason_for_blacklisted_tenant(tmp_path):
    blacklist_path = tmp_path / 'blacklist.json'
    blacklist_path.write_text(json.dumps([
        {
            'name': 'Jan Nowak',
            'reason': 'Repeated payment fraud'
        },
        {
            'name': 'Ewa Adamska',
            'reason': 'Forged identity documents'
        }
    ]), encoding='utf-8')

    manager = Manager(Parameters(blacklist_json_path=str(blacklist_path)))

    assert manager.check_tenant_blacklist('Jan Nowak') == 'Repeated payment fraud'
    assert manager.check_tenant_blacklist('Ewa Adamska') == 'Forged identity documents'


def test_check_tenant_blacklist_returns_none_for_tenant_not_on_blacklist(tmp_path):
    blacklist_path = tmp_path / 'blacklist.json'
    blacklist_path.write_text(json.dumps([
        {
            'name': 'Jan Nowak',
            'reason': 'Repeated payment fraud'
        }
    ]), encoding='utf-8')

    manager = Manager(Parameters(blacklist_json_path=str(blacklist_path)))

    assert manager.check_tenant_blacklist('Adam Kowalski') is None