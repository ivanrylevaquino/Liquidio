from datetime import date
from decimal import Decimal
from typing import List

from backend.app.models.line_item_budget import LineItemBudget
from backend.app.models.project import Project
from backend.app.schemas.expense import ExpenseValidationResult


class ExpenseValidationService:
    """
    Validates manual expense entries against DOST/CIT-U compliance rules.
    Produces error and warning message lists without rejecting the expense save.
    """
    @staticmethod
    def validate(
        project: Project,
        line_item: LineItemBudget,
        funding_source: str,
        expense_date: date,
        vendor_name: str,
        vendor_tin: str | None,
        vendor_address: str | None,
        payor_type: str,
        total_amount: Decimal,
    ) -> ExpenseValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Project timeline check
        if expense_date < project.start_date or expense_date > project.end_date:
            errors.append(
                f"Expense date ({expense_date.isoformat()}) is outside the project timeline "
                f"({project.start_date.isoformat()} to {project.end_date.isoformat()})."
            )

        # 2. Blank vendor check
        if not vendor_name or not vendor_name.strip():
            errors.append("Vendor name is blank.")

        # 3. Payor type check (INSTITUTION / BLANK / PERSONAL)
        if payor_type == "PERSONAL":
            errors.append("Ineligible for DOST reimbursement: payor type is PERSONAL.")
        elif payor_type == "BLANK":
            warnings.append("Payor type is BLANK; please verify payor details before liquidation.")

        # 4. TIN and address warnings
        if not vendor_tin or not vendor_tin.strip():
            warnings.append("Vendor TIN is missing.")
        if not vendor_address or not vendor_address.strip():
            warnings.append("Vendor address is missing.")

        # 5. Over-budget warning against remaining line-item balance
        if funding_source == "DOST_REIMBURSABLE":
            remaining = Decimal(str(line_item.remaining_dost))
            source_label = "DOST Reimbursable"
        else:
            remaining = Decimal(str(line_item.remaining_citu))
            source_label = "CIT-U Counterpart"

        if total_amount > remaining:
            warnings.append(
                f"Over-budget warning: amount (PHP {total_amount:,.2f}) exceeds remaining "
                f"{source_label} balance (PHP {remaining:,.2f}) for line item '{line_item.item_code}'."
            )

        return ExpenseValidationResult(
            is_valid_receipt=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
        )
