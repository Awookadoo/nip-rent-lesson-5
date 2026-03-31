from src.models import Apartment
from src.manager import Manager
from src.models import Parameters


def test_load_data():
    parameters = Parameters()
    manager = Manager(parameters)
    assert isinstance(manager.apartments, dict)
    assert isinstance(manager.tenants, dict)
    assert isinstance(manager.transfers, list)
    assert isinstance(manager.bills, list)

    for apartment_key, apartment in manager.apartments.items():
        assert isinstance(apartment, Apartment)
        assert apartment.key == apartment_key

def test_tenants_in_manager():
    parameters = Parameters()
    manager = Manager(parameters)
    assert len(manager.tenants) > 0
    names = [tenant.name for tenant in manager.tenants.values()]
    for tenant in ['Jan Nowak', 'Adam Kowalski', 'Ewa Adamska']:
        assert tenant in names

def test_if_tenants_have_valid_apartment_keys():
    parameters = Parameters()
    manager = Manager(parameters)
    assert manager.check_tenants_apartment_keys() == True

    manager.tenants['tenant-1'].apartment = 'invalid-key'
    assert manager.check_tenants_apartment_keys() == False
    
def test_get_apartment_costs():
    parameters = Parameters()
    manager = Manager(parameters)
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0
    assert manager.get_apartment_costs('apart-polanka', 2025, 2) == 0.0
    assert manager.get_apartment_costs('A1', 2024, 3) == None


def test_create_apartment_settlement_with_and_without_bills():
    from src.models import Bill

    parameters = Parameters()
    manager = Manager(parameters)

    manager.bills = []
    manager.transfers = []
    manager.apartments = {
        'apart-test': Apartment(
            key='apart-test',
            name='Test Apartment',
            location='Test Location',
            area_m2=50.0,
            rooms={}
        )
    }
    manager.tenants = {
        'tenant-A': type('T', (), {'name': 'Test Tenant', 'apartment': 'apart-test', 'rent_pln': 1000.0})()
    }

    manager.bills.append(Bill(apartment='apart-test', settlement_year=2025, settlement_month=5, amount_pln=200.0, date_due='2025-05-10', type='electricity'))
    manager.bills.append(Bill(apartment='apart-test', settlement_year=2025, settlement_month=5, amount_pln=150.0, date_due='2025-05-10', type='water'))
    manager.bills.append(Bill(apartment='apart-test', settlement_year=2025, settlement_month=6, amount_pln=300.0, date_due='2025-06-10', type='gas'))

    settlement_may = manager.create_apartment_settlement('apart-test', 2025, 5)

    assert settlement_may is not None
    assert settlement_may.apartment == 'apart-test'
    assert settlement_may.year == 2025
    assert settlement_may.month == 5
    assert settlement_may.total_bills_pln == 350.0
    assert settlement_may.total_rent_pln == 0.0
    assert settlement_may.total_due_pln == -350.0

    settlement_july = manager.create_apartment_settlement('apart-test', 2025, 7)
    assert settlement_july is not None
    assert settlement_july.total_bills_pln == 0.0
    assert settlement_july.total_rent_pln == 0.0
    assert settlement_july.total_due_pln == 0.0

    settlement_other = manager.create_apartment_settlement('apart-unknown', 2025, 5)
    assert settlement_other is None

    assert manager.get_apartment_costs('apart-test', 2025, 5) == 350.0
    assert manager.get_apartment_costs('apart-test', 2025, 7) == 0.0
    assert manager.get_apartment_transfers('apart-test', 2025, 5) == 0.0
    assert manager.get_apartment_transfers('apart-test', 2025, 7) == 0.0


def test_create_tenant_settlements_from_apartment():
    from src.models import Bill, Tenant

    parameters = Parameters()
    manager = Manager(parameters)
    manager.bills = []
    manager.transfers = []
    manager.apartments = {
        'apart-test': Apartment(
            key='apart-test',
            name='Test Apartment',
            location='Test Location',
            area_m2=50.0,
            rooms={}
        )
    }

    # 2 tenants
    manager.tenants = {
        'tenant-A': Tenant(
            name='Tenant A',
            apartment='apart-test',
            room='room-A',
            rent_pln=1000.0,
            deposit_pln=2000.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        ),
        'tenant-B': Tenant(
            name='Tenant B',
            apartment='apart-test',
            room='room-B',
            rent_pln=1200.0,
            deposit_pln=2400.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        )
    }

    manager.bills.append(Bill(apartment='apart-test', settlement_year=2025, settlement_month=5, amount_pln=400.0, date_due='2025-05-10', type='electricity'))

    apt_settlement = manager.create_apartment_settlement('apart-test', 2025, 5)
    assert apt_settlement is not None
    tenant_settlements = manager.create_tenant_settlements_from_apartment_settlement(apt_settlement)

    assert len(tenant_settlements) == 2
    assert tenant_settlements[0].tenant in ['Tenant A', 'Tenant B']
    assert tenant_settlements[1].tenant in ['Tenant A', 'Tenant B']
    assert tenant_settlements[0].apartment_settlement == 'apart-test'
    assert tenant_settlements[1].apartment_settlement == 'apart-test'
    assert tenant_settlements[0].month == 5
    assert tenant_settlements[0].year == 2025
    assert tenant_settlements[0].bills_pln == 200.0
    assert tenant_settlements[1].bills_pln == 200.0
    assert tenant_settlements[0].total_due_pln == -200.0
    assert tenant_settlements[1].total_due_pln == -200.0

    # 1 tenant case
    manager.tenants = {
        'tenant-C': Tenant(
            name='Tenant C',
            apartment='apart-test',
            room='room-C',
            rent_pln=1300.0,
            deposit_pln=2600.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31'
        )
    }
    manager.bills = [Bill(apartment='apart-test', settlement_year=2025, settlement_month=6, amount_pln=300.0, date_due='2025-06-10', type='water')]

    apt_settlement_single = manager.create_apartment_settlement('apart-test', 2025, 6)
    assert apt_settlement_single is not None
    tenant_settlements_single = manager.create_tenant_settlements_from_apartment_settlement(apt_settlement_single)
    assert len(tenant_settlements_single) == 1
    assert tenant_settlements_single[0].tenant == 'Tenant C'
    assert tenant_settlements_single[0].bills_pln == 300.0
    assert tenant_settlements_single[0].total_due_pln == -300.0

    # no tenants case
    manager.tenants = {}
    manager.bills = [Bill(apartment='apart-test', settlement_year=2025, settlement_month=7, amount_pln=250.0, date_due='2025-07-10', type='gas')]
    apt_settlement_empty = manager.create_apartment_settlement('apart-test', 2025, 7)
    assert apt_settlement_empty is not None
    tenant_settlements_empty = manager.create_tenant_settlements_from_apartment_settlement(apt_settlement_empty)
    assert tenant_settlements_empty == []