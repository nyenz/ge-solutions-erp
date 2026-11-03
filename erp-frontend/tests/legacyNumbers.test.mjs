import test from 'node:test';
import assert from 'node:assert/strict';
import { placeInitials, invoicePrefix, paperPart, madeInvoiceNumber, ninFromName } from '../src/utils/legacyNumbers.js';
import { withCommas, typeMoney } from '../src/utils/moneyTyping.js';

test('initials of a place', () => {
    assert.equal(placeInitials('Kamuli'), 'KAM');
    assert.equal(placeInitials('namwendwa'), 'NAM');
    assert.equal(placeInitials('Central Division'), 'CD');
    assert.equal(placeInitials('  '), '');
    assert.equal(invoicePrefix('Jinja', 'Central Division'), 'JIN-CD');
    assert.equal(invoicePrefix('Jinja', ''), '');
});

test('the made invoice number (the examples David saw)', () => {
    assert.equal(madeInvoiceNumber('Kamuli', 'Namwendwa', '7'), 'KAM-NAM-0007');
    assert.equal(madeInvoiceNumber('Kamuli', 'Bugulumbya', '7'), 'KAM-BUG-0007');
    assert.equal(madeInvoiceNumber('Iganga', 'Nakalama', '123'), 'IGA-NAK-0123');
    assert.equal(madeInvoiceNumber('Jinja', 'Central Division', '45'), 'JIN-CD-0045');
    assert.equal(madeInvoiceNumber('Jinja', 'Central Division', ''), '');
    assert.equal(paperPart('12a'), '012A');
    assert.equal(paperPart('12345'), '12345');
});

test('a NIN made from the name', () => {
    assert.equal(ninFromName('  namuganza   sarah '), 'NAMUGANZA SARAH');
});

test('money boxes show commas while typing and keep the cursor', () => {
    assert.equal(withCommas('1500000'), '1,500,000');
    assert.equal(withCommas('0'), '0');
    assert.equal(withCommas('007'), '7');
    assert.equal(withCommas(''), '');
    assert.equal(withCommas('15000.00'), '15,000');
    assert.equal(withCommas(1500000), '1,500,000');
    const r = typeMoney('150000', 6);
    assert.deepEqual(r, { ok: true, digits: '150000', shown: '150,000', caret: 7 });
    // a digit typed in the middle: "1,5|00,000" + 9 -> cursor stays after the 9
    const m = typeMoney('1,59|00,000'.replace('|', ''), 4);
    assert.equal(m.shown, '15,900,000');
    assert.equal(m.shown.slice(0, m.caret).replace(/\D/g, ''), '159');
    assert.equal(typeMoney('1.5', 3).ok, false);
    assert.equal(typeMoney('12a', 3).ok, false);
});
