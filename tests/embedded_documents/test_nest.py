import datetime
from typing import List

import pytest

import mongoz
from mongoz import Document, EmbeddedDocument
from tests.conftest import client

pytestmark = pytest.mark.anyio


class EmployeeSupervisor(EmbeddedDocument):
    supervisor: mongoz.ObjectId = mongoz.ObjectId()  # Object id of employee document.
    effective_from: datetime.datetime = mongoz.DateTime(auto_now=True)
    effective_to: datetime.datetime = mongoz.DateTime(auto_now_add=True)


class Employee(Document):
    full_name: str = mongoz.String(max_length=255)
    employee_code: str = mongoz.String(max_length=255)
    date_of_joining: datetime.datetime = mongoz.DateTime(null=True)
    e_mail: str = mongoz.String(null=True)
    mobile_no: str = mongoz.String(null=True)
    supervisors: List[EmployeeSupervisor] = mongoz.Array(EmployeeSupervisor)

    class Meta:
        registry = client
        database = "test_db"


async def test_embedded_model() -> None:
    sv = EmployeeSupervisor(
        supervisor=mongoz.ObjectId(),
        effective_from=datetime.datetime.now(),
        effective_to=datetime.datetime.now(),
    )

    employee = await Employee.objects.create(
        full_name="A name", employee_code="1234", supervisors=[sv]
    )

    assert employee.supervisors[0].supervisor == sv.supervisor
