import pytest
from io import BytesIO
import openpyxl
from django.contrib.auth.models import User, Group
from rest_framework.test import APIClient

def make_product_xlsx(rows):
    wb = openpyxl.Workbook(); ws = wb.active
    ws.append(['product_no', 'model', 'name', 'spec', 'default_price', 'default_cost_price'])
    for r in rows:
        ws.append(r)
    buf = BytesIO(); wb.save(buf); buf.seek(0)
    return buf

@pytest.fixture
def admin_client(db):
    u = User.objects.create_user('admin1', password='pw123456')
    u.groups.add(Group.objects.get(name='admin'))
    c = APIClient(); c.force_authenticate(u); return c

def test_import_products_upsert(admin_client):
    buf = make_product_xlsx([
        ['P001', 'M1', '名片', '90x54', '0.10', '0.50'],
        ['P002', 'M2', '传单', 'A5', '0.20', '1.00'],
    ])
    r = admin_client.post('/api/basic-info/products/import/', {'file': buf}, format='multipart')
    assert r.status_code == 200
    assert r.data['data']['success_count'] == 2 and r.data['data']['fail_count'] == 0

def test_import_products_repeat_upserts(admin_client, db):
    from apps.basic_info.models import Product
    buf = make_product_xlsx([['P001', 'M1', '名片', '', '0.10', '0.50']])
    admin_client.post('/api/basic-info/products/import/', {'file': buf}, format='multipart')
    buf2 = make_product_xlsx([['P001', 'M1', '名片彩版', '', '0.12', '0.55']])
    r = admin_client.post('/api/basic-info/products/import/', {'file': buf2}, format='multipart')
    assert r.data['data']['success_count'] == 1
    assert Product.objects.get(product_no='P001').name == '名片彩版'

def test_import_collects_failures(admin_client):
    buf = make_product_xlsx([
        ['', 'M', '无编号', '', '0.1', '0.5'],          # 缺 product_no
        ['P001', 'M', '名片', '', '0.1', '0.5'],
    ])
    r = admin_client.post('/api/basic-info/products/import/', {'file': buf}, format='multipart')
    assert r.data['data']['fail_count'] == 1
    assert r.data['data']['failures'][0]['row'] == 2  # Excel 行号

def test_import_template_download(admin_client):
    r = admin_client.get('/api/basic-info/products/import-template/')
    assert r.status_code == 200
    assert r['Content-Type'].find('spreadsheet') >= 0 or r['Content-Type'].find('excel') >= 0
