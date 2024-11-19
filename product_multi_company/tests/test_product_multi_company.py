# Copyright 2015-2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2021 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.exceptions import AccessError
from odoo.tests import common

from .common import ProductMultiCompanyCommon


class TestProductMultiCompany(ProductMultiCompanyCommon, common.TransactionCase):
    def test_create_product(self):
        product = self.env["product.product"].create({"name": "Test"})
        company = self.env.company
        self.assertTrue(company.id in product.company_ids.ids)

    def test_company_none(self):
        self.assertFalse(self.product_company_none.company_id)
        # All of this should be allowed
        self.product_company_none.with_user(
            self.user_company_1.id
        ).description_sale = "Test 1"
        self.product_company_none.with_user(
            self.user_company_2.id
        ).description_sale = "Test 2"

    def test_company_1(self):
        self.assertEqual(
            self.product_company_1.with_user(self.user_company_1).company_id,
            self.company_1,
        )
        # All of this should be allowed
        self.product_company_1.with_user(
            self.user_company_1
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_1
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_2.with_user(
                self.user_company_1
            ).description_sale = "Test 3"

    def test_company_2(self):
        self.assertEqual(
            self.product_company_2.with_user(self.user_company_2).company_id,
            self.company_2,
        )
        # All of this should be allowed
        self.product_company_2.with_user(
            self.user_company_2
        ).description_sale = "Test 1"
        self.product_company_both.with_user(
            self.user_company_2
        ).description_sale = "Test 2"
        # And this one not
        with self.assertRaises(AccessError):
            self.product_company_1.with_user(
                self.user_company_2
            ).description_sale = "Test 3"

    def test_search_product(self):
        """Products with no company are shared across companies but we need to convert
        those queries with an or operator"""
        expected_products = (
            self.product_company_both
            + self.product_company_1
            + self.product_company_none
        )
        searched_templates = self.env["product.template"].search(
            [
                ("company_id", "in", [self.company_1.id, False]),
                ("id", "in", expected_products.product_tmpl_id.ids),
            ]
        )
        self.assertEqual(searched_templates, expected_products.product_tmpl_id)
        searched_products = self.product_obj.search(
            [
                ("company_id", "in", [self.company_1.id, False]),
                ("id", "in", expected_products.ids),
            ]
        )
        self.assertEqual(searched_products, expected_products)

    def test_uninstall(self):
        from ..hooks import uninstall_hook

        uninstall_hook(self.env.cr, None)
        rule = self.env.ref("product.product_comp_rule")
        domain = (
            " ['|', ('company_id', '=', user.company_id.id), "
            "('company_id', '=', False)]"
        )
        self.assertEqual(rule.domain_force, domain)
