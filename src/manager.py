from src.models import Apartment, Bill, Parameters, Tenant, Transfer, ApartmentSettlement, TenantSettlement


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True
    
    def get_apartment_costs(self, apartment_key, year=0, month=0):
        if apartment_key not in self.apartments:
            return None
        costs = 0
        if year == 0:
            for bill in self.bills:
                if bill.apartment == apartment_key:
                    costs += bill.amount_pln
        elif month == 0:
            for bill in self.bills:
                if bill.apartment == apartment_key and bill.settlement_year == year:
                    costs += bill.amount_pln
        elif month >= 1 or month <= 12:
            for bill in self.bills:
                if bill.apartment == apartment_key and bill.settlement_month == month and bill.settlement_year == year:
                    costs += bill.amount_pln
        return costs

    def get_tenant_rent(self, apartment_key):
        rent = 0
        for tenant in self.tenants.values():
            if tenant.apartment == apartment_key:
                rent += tenant.rent_pln

        return rent

    def get_apartment_transfers(self, apartment_key, year=0, month=0):
        if apartment_key not in self.apartments:
            return None

        transfers_sum = 0
        for transfer in self.transfers:
            tenant_obj = self.tenants.get(transfer.tenant)
            if not tenant_obj or tenant_obj.apartment != apartment_key:
                continue

            if year == 0:
                transfers_sum += transfer.amount_pln
            elif month == 0 and transfer.settlement_year == year:
                transfers_sum += transfer.amount_pln
            elif transfer.settlement_year == year and transfer.settlement_month == month:
                transfers_sum += transfer.amount_pln

        return transfers_sum

    def create_apartment_settlement(self, apartment_key, year, month):
        if apartment_key not in self.apartments:
            return None

        bills = self.get_apartment_costs(apartment_key, year, month)
        transfers = self.get_apartment_transfers(apartment_key, year, month)

        if bills is None or transfers is None:
            return None

        balance = transfers - bills

        return ApartmentSettlement(
            apartment=apartment_key,
            year=year,
            month=month,
            total_rent_pln=transfers,
            total_bills_pln=bills,
            total_due_pln=balance
        )

    def bilans(self, apartment_key, year, month):
        bills = self.get_apartment_costs(apartment_key, year, month)
        rent = self.get_tenant_rent(apartment_key)

        return ApartmentSettlement(
            apartment=apartment_key,
            year=year,
            month=month,
            total_bills_pln=bills,
            total_rent_pln=rent,
            total_due_pln=rent + bills
        )

    def create_tenant_settlements_from_apartment_settlement(self, apartment_settlement):
        if not apartment_settlement:
            return []

        apartment_key = apartment_settlement.apartment
        if apartment_key not in self.apartments:
            return []

        tenants = [t for t in self.tenants.values() if t.apartment == apartment_key]
        if not tenants:
            return []

        per_tenant_bills = apartment_settlement.total_bills_pln / len(tenants)
        results = []

        for tenant in tenants:
            results.append(TenantSettlement(
                tenant=tenant.name,
                apartment_settlement=apartment_key,
                month=apartment_settlement.month,
                year=apartment_settlement.year,
                rent_pln=tenant.rent_pln,
                bills_pln=per_tenant_bills,
                total_due_pln=-per_tenant_bills,
                balance_pln=-per_tenant_bills
            ))

        return results