from typing import List

import pydantic
import pytest

import mongoz
from mongoz import Index
from tests.conftest import client

pytestmark = pytest.mark.anyio
pydantic_version = pydantic.__version__[:3]

indexes = [
    Index("name", unique=True),
    Index("year", unique=True),
]


class CompanyBranch(mongoz.EmbeddedDocument):
    """
    **Summary** This Class represents the company branch.
        **Fields:**
            - name (str): It contains the branch name.
            - address (str): It contains the branch address.
    """

    name: str = mongoz.String(max_length=100, null=True)
    address: str = mongoz.String(max_length=100, null=True)


class Company(mongoz.Document):
    """
        **Summary** This Class represents the company.
            **Fields:**
                - code (str): It contains the company code.
                - name (str): It contains the company name.
                - branches (List[CompanyBranch]): It contains the embedded \
                        documents of company_branch model.
    """

    code: str = mongoz.String()
    display_name: str = mongoz.String(null=True)
    branches: List[CompanyBranch] = mongoz.Array(CompanyBranch, null=True)

    def __str__(self):
        return f"<{self.display_name}: ({self.code})>"

    class Meta:
        registry = client
        database = "test_db"
        collection = "dymmond_companies"
        indexes = [
            mongoz.Index("code", unique=True),
        ]


async def test_create_company_with_collection():
    company = await Company.objects.create(code="123", display_name="Dymmond")

    assert str(company) == "<Dymmond: (123)>"
