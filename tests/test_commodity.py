# coding=utf-8
from __future__ import unicode_literals
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import pytest
from piecash import Transaction, Split, GncImbalanceError, GncValidationError, Price, Commodity, GnucashException
from piecash.core.commodity import GncPriceError
from test_helper import db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic

# dummy line to avoid removing unused symbols

a = db_sqlite_uri, db_sqlite, new_book, new_book_USD, book_uri, book_basic


class TestCommodity_create_commodity(object):
    def test_create_commodity(self, book_basic):
        assert len(book_basic.commodities)==2
        cdty = Commodity(namespace="AMEX",mnemonic="APPLE",fullname="Apple", book=book_basic)
        book_basic.flush()
        assert len(book_basic.commodities)==3

        with pytest.raises(GnucashException):
            cdty.base_currency

        cdty["quoted_currency"]="EUR"
        assert cdty.base_currency==book_basic.commodities(mnemonic="EUR")

    def test_base_currency_commodity(self, book_basic):
        cdty = Commodity(namespace="AMEX",mnemonic="APPLE",fullname="Apple", book=book_basic)

        with pytest.raises(GnucashException):
            cdty.base_currency

        # should trigger creation of USD currency
        cdty["quoted_currency"]="USD"
        assert cdty.base_currency.mnemonic=='USD'
        book_basic.flush()
        assert cdty.base_currency ==book_basic.currencies(mnemonic="USD")

        cdty["quoted_currency"]="EUR"
        assert cdty.base_currency==book_basic.currencies(mnemonic="EUR")

    def test_base_currency_commodity_no_book(self, book_basic):
        cdty = Commodity(namespace="AMEX",mnemonic="APPLE",fullname="Apple")

        with pytest.raises(GnucashException):
            cdty.base_currency


    def test_base_currency_currency(self, book_basic):
        cdty = book_basic.currencies(mnemonic="USD")

        assert cdty.base_currency.mnemonic=="EUR"


class TestCommodity_create_prices(object):
    def test_create_basicprice(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        USD = book_basic.currencies(mnemonic="USD")
        p = Price(commodity=USD, currency=EUR, date=datetime(2014, 2, 22), value=Decimal('0.54321'))

        # check price exist
        np = USD.prices.first()
        assert np is p
        assert repr(p)=="Price<2014-02-22 : 0.54321 EUR/USD>"

        p2 = Price(commodity=USD, currency=EUR, date=datetime(2014, 2, 21), value=Decimal('0.12345'))
        book_basic.flush()
        assert p.value + p2.value == Decimal("0.66666")
        assert len(USD.prices.all()) == 2

    def test_create_duplicateprice(self, book_basic):
        EUR = book_basic.commodities(namespace="CURRENCY")
        USD = book_basic.currencies(mnemonic="USD")
        p = Price(commodity=USD, currency=EUR, date=datetime(2014, 2, 22), value=Decimal('0.54321'))
        p1 = Price(commodity=USD, currency=EUR, date=datetime(2014, 2, 22), value=Decimal('0.12345'))

        book_basic.flush()
        assert USD.prices.filter_by(value=Decimal('0')).all()==[]
        assert USD.prices.filter_by(value=Decimal('0.12345')).one()==p1

        from sqlalchemy.orm.exc import NoResultFound
        with pytest.raises(NoResultFound):
            USD.prices.filter_by(value=Decimal('0.123')).one()

    def test_update_prices(self,book_basic):
        USD = book_basic.currencies(mnemonic="USD")
        # book_basic.flush()
        USD.update_prices()
        USD.update_prices()

        assert len(list(USD.prices))<7
        assert USD.prices.first().commodity is USD
        assert USD.guid is None

        CAD = book_basic.currencies(mnemonic="CAD")
        # book_basic.flush()
        CAD.update_prices()
        assert len(list(CAD.prices))<7
        assert CAD.prices.first().commodity is CAD
        assert CAD.guid is None
        book_basic.flush()

        assert len(book_basic.prices)<14

    def test_price_update_on_commodity_no_book(self, book_basic):
        cdty = Commodity(namespace="AMEX",mnemonic="APPLE",fullname="Apple")

        with pytest.raises(GncPriceError):
            cdty.update_prices()

