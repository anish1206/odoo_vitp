from sqlalchemy import func, select

from app.core.default_data import DEFAULT_EXPENSE_CATEGORIES
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models import Company, ExpenseCategory, User, UserRole

PASSWORD = "DemoPass123!"

ADMIN_EMAIL = "demo.admin.phase4@example.com"
APPROVER_EMAIL = "demo.approver.phase4@example.com"
EMPLOYEE_EMAIL = "demo.employee.phase4@example.com"


def upsert_user(db, *, email, first_name, last_name, role, is_approver, manager_id, company_id):
    user = db.scalar(select(User).where(User.email == email))
    hashed = get_password_hash(PASSWORD)

    if user is None:
        user = User(
            company_id=company_id,
            email=email,
            hashed_password=hashed,
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_approver=is_approver,
            is_active=True,
            manager_id=manager_id,
        )
        db.add(user)
        db.flush()
        return user

    user.company_id = company_id
    user.first_name = first_name
    user.last_name = last_name
    user.role = role
    user.is_approver = is_approver
    user.is_active = True
    user.manager_id = manager_id
    user.hashed_password = hashed
    db.flush()
    return user


with SessionLocal() as db:
    company = db.scalar(select(Company).order_by(Company.id.asc()))

    if company is None:
        company = Company(name="Phase4 Demo Company", country_code="IN", base_currency="INR")
        db.add(company)
        db.flush()

    category_count = db.scalar(
        select(func.count()).select_from(ExpenseCategory).where(ExpenseCategory.company_id == company.id)
    )
    if category_count == 0:
        for category in DEFAULT_EXPENSE_CATEGORIES:
            db.add(
                ExpenseCategory(
                    company_id=company.id,
                    name=category["name"],
                    code=category["code"],
                    description=category["description"],
                )
            )
        db.flush()

    admin = upsert_user(
        db,
        email=ADMIN_EMAIL,
        first_name="Demo",
        last_name="Admin",
        role=UserRole.ADMIN,
        is_approver=True,
        manager_id=None,
        company_id=company.id,
    )

    approver = upsert_user(
        db,
        email=APPROVER_EMAIL,
        first_name="Demo",
        last_name="Approver",
        role=UserRole.EMPLOYEE,
        is_approver=True,
        manager_id=None,
        company_id=company.id,
    )

    employee = upsert_user(
        db,
        email=EMPLOYEE_EMAIL,
        first_name="Demo",
        last_name="Employee",
        role=UserRole.EMPLOYEE,
        is_approver=False,
        manager_id=approver.id,
        company_id=company.id,
    )

    db.commit()

    print("seeded_company", company.id, company.name)
    print("admin", admin.email)
    print("approver", approver.email)
    print("employee", employee.email)
